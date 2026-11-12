"""Load the concepts of an ESRS XBRL taxonomy package that can be tagged in a report."""

import io
import os
import posixpath
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple
from xml.etree.ElementTree import Element, ParseError

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import fromstring, iterparse

from report_analyst.models.taxonomy import EsrsReference, Taxonomy, TaxonomyConcept, TaxonomyOption

TAXONOMY_PATH_ENV = "ESRS_TAXONOMY_PATH"

XS = "{http://www.w3.org/2001/XMLSchema}"
LINK = "{http://www.xbrl.org/2003/linkbase}"
XLINK = "{http://www.w3.org/1999/xlink}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
XBRLI = "{http://www.xbrl.org/2003/instance}"
ENUM2 = "{http://xbrl.org/2020/extensible-enumerations-2.0}"
PACKAGE = "{http://xbrl.org/2016/taxonomy-package}"
CATALOG = "{urn:oasis:names:tc:entity:xmlns:xml:catalog}"

LINKBASE_KINDS = {
    f"http://www.xbrl.org/2003/role/{kind}LinkbaseRef": kind for kind in ("label", "reference", "presentation", "definition")
}
STANDARD_LABEL = "http://www.xbrl.org/2003/role/label"
DOMAIN_MEMBER = "http://xbrl.org/int/dim/arcrole/domain-member"
# EFRAG references other laws too, such as SFDR. This name marks a reference to the ESRS.
ESRS_REFERENCE = "ESRS"

# Kinds by data type name. The numeric types are listed because the schemas that define
# them as numbers are on xbrl.org, outside the package.
KINDS = {
    "textBlockItemType": "narrative",
    "booleanItemType": "yes/no",
    "enumerationItemType": "menu",
    "enumerationSetItemType": "menu",
    "stringItemType": "text",
    "dateItemType": "date",
    "gYearItemType": "date",
    **dict.fromkeys(
        [
            "decimalItemType",
            "energyItemType",
            "ghgEmissionsItemType",
            "integerItemType",
            "massItemType",
            "monetaryItemType",
            "percentItemType",
            "volumeItemType",
        ],
        "number",
    ),
}

REFERENCE_PARTS = {
    "Section": "section",
    "Number": "disclosure_requirement",
    "Paragraph": "paragraph",
    "Subparagraph": "subparagraph",
    "Clause": "clause",
    "DatapointId": "datapoint_id",
    "URI": "url",
}


class TaxonomyUnavailableError(Exception):
    """The taxonomy package is not set up or cannot be read."""


def load_esrs_taxonomy(path: str | Path | None = None, language: str = "en") -> Taxonomy:
    """Load a taxonomy package from a zip or an unzipped folder, by default from ESRS_TAXONOMY_PATH."""
    path = path or os.getenv(TAXONOMY_PATH_ENV)
    if not path:
        raise TaxonomyUnavailableError(f"Set {TAXONOMY_PATH_ENV} to the ESRS taxonomy package downloaded from EFRAG.")
    path = Path(path)
    if not path.exists():
        raise TaxonomyUnavailableError(f"No ESRS taxonomy package found at {path}.")
    try:
        package = _Package(path)
        return Taxonomy(
            identifier=package.index.findtext(f"{PACKAGE}identifier"),
            name=package.index.findtext(f"{PACKAGE}name"),
            version=package.index.findtext(f"{PACKAGE}version"),
            concepts=_complete_entry_point(package).concepts(language),
        )
    except (OSError, ParseError, DefusedXmlException, zipfile.BadZipFile) as error:
        raise TaxonomyUnavailableError(f"Could not read the ESRS taxonomy package at {path}: {error}") from error


class _Package:
    """The files of a taxonomy package, read from a zip or a folder."""

    def __init__(self, path: Path):
        base = zipfile.Path(path) if path.is_file() else path
        # A zipped package keeps META-INF inside one top-level folder.
        roots = [base] if (base / "META-INF").is_dir() else [c for c in base.iterdir() if (c / "META-INF").is_dir()]
        if len(roots) != 1:
            raise TaxonomyUnavailableError(f"{path} is not a taxonomy package. It needs one META-INF folder.")
        self.root = roots[0]
        self.index = self.parse("META-INF/taxonomyPackage.xml")
        catalog = self.parse("META-INF/catalog.xml")
        self.rewrites = [
            (rule.get("uriStartString"), rule.get("rewritePrefix")) for rule in catalog.iter(f"{CATALOG}rewriteURI")
        ]

    def read(self, file: str) -> bytes:
        return self.root.joinpath(*file.split("/")).read_bytes()

    def parse(self, file: str) -> Element:
        return fromstring(self.read(file))

    def locate(self, href: str, base_file: str) -> str | None:
        """The package file an href points to, or None when it is outside the package."""
        if "://" not in href:
            return posixpath.normpath(posixpath.join(posixpath.dirname(base_file), href))
        for start, prefix in self.rewrites:
            if href.startswith(start):
                return posixpath.normpath(posixpath.join("META-INF", prefix + href[len(start) :]))
        return None


def _complete_entry_point(package: _Package) -> "_Dts":
    """The first entry point with labels, references, presentation and definition.

    A package can also offer smaller entry points, for example one with only concepts and labels.
    """
    for document in package.index.iter(f"{PACKAGE}entryPointDocument"):
        file = package.locate(document.get("href"), "META-INF/taxonomyPackage.xml")
        if file is None:
            raise TaxonomyUnavailableError(f"The package catalog does not say where {document.get('href')} is.")
        dts = _Dts(package, file)
        if set(dts.linkbases.values()) == set(LINKBASE_KINDS.values()):
            return dts
    raise TaxonomyUnavailableError("No entry point in the package has labels, references, presentation and definition.")


class _SchemaElement(NamedTuple):
    """An element from a schema, with the namespaces needed to name it and read its menu domain."""

    element: Element
    namespace: str
    prefix: str | None
    namespaces: dict[str, str]

    @property
    def qname(self) -> str:
        if self.prefix is None:
            raise TaxonomyUnavailableError(f"The schema gives no prefix for {self.namespace}.")
        return f"{self.prefix}:{self.element.get('name')}"


class _Dts:
    """What an entry point brings in, known in XBRL as the DTS.

    That is its schemas, the schemas they import and their linkbases, limited to files inside the package.
    """

    def __init__(self, package: _Package, entry_file: str):
        self.package = package
        self.elements: dict[str, _SchemaElement] = {}
        self.keys_by_name: dict[tuple[str, str], str] = {}
        self.group_names: dict[str, str] = {}
        self.linkbases: dict[str, str] = {}
        queue, seen = [entry_file], set()
        while queue:
            file = queue.pop()
            if file not in seen:
                seen.add(file)
                queue.extend(self._add_schema(file))

    def _add_schema(self, file: str) -> list[str]:
        data = self.package.read(file)
        schema = fromstring(data)
        namespace = schema.get("targetNamespace")
        namespaces = _namespaces(data)
        prefix = next((name for name, uri in namespaces.items() if uri == namespace), None)
        for element in schema.iterfind(f"{XS}element"):
            key = f"{file}#{element.get('id')}"
            self.elements[key] = _SchemaElement(element, namespace, prefix, namespaces)
            self.keys_by_name[namespace, element.get("name")] = key
        for role in schema.iter(f"{LINK}roleType"):
            self.group_names[role.get("roleURI")] = role.findtext(f"{LINK}definition")
        for ref in schema.iter(f"{LINK}linkbaseRef"):
            linkbase = self.package.locate(ref.get(f"{XLINK}href"), file)
            if linkbase and ref.get(f"{XLINK}role") in LINKBASE_KINDS:
                self.linkbases[linkbase] = LINKBASE_KINDS[ref.get(f"{XLINK}role")]
        imports = [*schema.iterfind(f"{XS}import"), *schema.iterfind(f"{XS}include")]
        located = (self.package.locate(item.get("schemaLocation"), file) for item in imports if item.get("schemaLocation"))
        return [schema_file for schema_file in located if schema_file]

    def relationships(self, kind: str, arc_name: str):
        """Yield (link role, arc, source, target) for each arc, with locators turned into element keys."""
        files = [file for file, linkbase_kind in self.linkbases.items() if linkbase_kind == kind]
        for file in files:
            for link in self.package.parse(file):
                if link.get(f"{XLINK}type") != "extended":
                    continue
                nodes = self._nodes(link, file)
                for arc in link.iterfind(f"{LINK}{arc_name}"):
                    if arc.get("use") == "prohibited":
                        raise TaxonomyUnavailableError(
                            "The taxonomy removes relationships with prohibited arcs. This loader does not support that yet."
                        )
                    for source in nodes[arc.get(f"{XLINK}from")]:
                        for target in nodes[arc.get(f"{XLINK}to")]:
                            yield link.get(f"{XLINK}role"), arc, source, target

    def _nodes(self, link: Element, file: str) -> dict[str, list]:
        """What each label in an extended link points to: element keys for locators, the element for resources."""
        nodes = defaultdict(list)
        for node in link:
            if node.get(f"{XLINK}type") == "locator":
                nodes[node.get(f"{XLINK}label")].append(self._element_key(node.get(f"{XLINK}href"), file))
            elif node.get(f"{XLINK}type") == "resource":
                nodes[node.get(f"{XLINK}label")].append(node)
        return nodes

    def _element_key(self, href: str, linkbase_file: str) -> str | None:
        schema, _, element_id = href.partition("#")
        schema_file = self.package.locate(schema, linkbase_file)
        return f"{schema_file}#{element_id}" if schema_file else None

    def concepts(self, language: str) -> list[TaxonomyConcept]:
        labels = self._labels(language)
        references = self._esrs_references()
        groups = self._groups()
        members = self._domain_members()

        def label(key):
            if key not in labels:
                raise TaxonomyUnavailableError(f"{self.elements[key].qname} has no {language} label.")
            return labels[key]

        concepts = []
        for key, concept in self.elements.items():
            element = concept.element
            if element.get("substitutionGroup") != "xbrli:item" or element.get("abstract") == "true":
                continue
            kind = _kind(concept)
            options = self._options(concept, members) if kind == "menu" else []
            concepts.append(
                TaxonomyConcept(
                    name=concept.qname,
                    label=label(key),
                    kind=kind,
                    data_type=element.get("type"),
                    period_type=element.get(f"{XBRLI}periodType"),
                    group=groups.get(key),
                    esrs_references=list(dict.fromkeys(references[key])),
                    options_domain=element.get(f"{ENUM2}domain"),
                    options=[TaxonomyOption(name=self.elements[member].qname, label=label(member)) for member in options],
                )
            )
        return concepts

    def _labels(self, language: str) -> dict[str, str]:
        return {
            concept: label.text
            for _, _, concept, label in self.relationships("label", "labelArc")
            if label.get(f"{XLINK}role") == STANDARD_LABEL and label.get(XML_LANG) == language
        }

    def _esrs_references(self) -> dict[str, list[EsrsReference]]:
        references = defaultdict(list)
        for _, _, concept, reference in self.relationships("reference", "referenceArc"):
            parts = {child.tag.split("}")[1]: child.text for child in reference}
            if parts.get("Name") == ESRS_REFERENCE:
                fields = {field: parts[part] for part, field in REFERENCE_PARTS.items() if part in parts}
                references[concept].append(EsrsReference(**fields))
        return references

    def _groups(self) -> dict[str, str]:
        """The presentation group that first shows each concept."""
        groups = {}
        for role, _, parent, child in self.relationships("presentation", "presentationArc"):
            for concept in (parent, child):
                groups.setdefault(concept, self.group_names.get(role))
        return groups

    def _domain_members(self) -> dict[str, dict[str, list[tuple[float, str]]]]:
        """Members under each parent, per link role, with their order."""
        members = defaultdict(lambda: defaultdict(list))
        for role, arc, parent, child in self.relationships("definition", "definitionArc"):
            if arc.get(f"{XLINK}arcrole") == DOMAIN_MEMBER:
                members[role][parent].append((float(arc.get("order", 0)), child))
        return members

    def _options(self, concept: _SchemaElement, members) -> list[str]:
        """Element keys of a menu's options, in taxonomy order. Empty when the options are outside the package."""
        domain_prefix, _, domain_name = concept.element.get(f"{ENUM2}domain").partition(":")
        domain = self.keys_by_name.get((concept.namespaces.get(domain_prefix), domain_name))
        if domain is None:
            return []
        tree = members[concept.element.get(f"{ENUM2}linkrole")]
        found = [domain] if concept.element.get(f"{ENUM2}headUsable") == "true" else []

        def visit(parent):
            for _, child in sorted(tree[parent]):
                found.append(child)
                visit(child)

        visit(domain)
        return found


def _kind(concept: _SchemaElement) -> str:
    data_type = concept.element.get("type")
    kind = KINDS.get(data_type.split(":")[-1])
    if kind is None:
        raise TaxonomyUnavailableError(f"{concept.qname} has a data type this loader does not know yet: {data_type}.")
    return kind


def _namespaces(data: bytes) -> dict[str, str]:
    """Prefix to namespace, as declared in an XML file."""
    namespaces = {}
    for _, (prefix, uri) in iterparse(io.BytesIO(data), events=["start-ns"]):
        namespaces.setdefault(prefix, uri)
    return namespaces
