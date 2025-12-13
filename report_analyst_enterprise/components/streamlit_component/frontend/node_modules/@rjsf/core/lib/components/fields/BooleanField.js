import { jsx as _jsx } from "react/jsx-runtime";
import { getWidget, getUiOptions, optionsList, TranslatableString, } from '@rjsf/utils';
import isObject from 'lodash-es/isObject.js';
/** The `BooleanField` component is used to render a field in the schema is boolean. It constructs `enumOptions` for the
 * two boolean values based on the various alternatives in the schema.
 *
 * @param props - The `FieldProps` for this template
 */
function BooleanField(props) {
    const { schema, name, uiSchema, idSchema, formData, registry, required, disabled, readonly, hideError, autofocus, title, onChange, onFocus, onBlur, rawErrors, } = props;
    const { title: schemaTitle } = schema;
    const { widgets, formContext, translateString, globalUiOptions } = registry;
    const { widget = 'checkbox', title: uiTitle, 
    // Unlike the other fields, don't use `getDisplayLabel()` since it always returns false for the boolean type
    label: displayLabel = true, ...options } = getUiOptions(uiSchema, globalUiOptions);
    const Widget = getWidget(schema, widget, widgets);
    const yes = translateString(TranslatableString.YesLabel);
    const no = translateString(TranslatableString.NoLabel);
    let enumOptions;
    const label = uiTitle ?? schemaTitle ?? title ?? name;
    if (Array.isArray(schema.oneOf)) {
        enumOptions = optionsList({
            oneOf: schema.oneOf
                .map((option) => {
                if (isObject(option)) {
                    return {
                        ...option,
                        title: option.title || (option.const === true ? yes : no),
                    };
                }
                return undefined;
            })
                .filter((o) => o), // cast away the error that typescript can't grok is fixed
        }, uiSchema);
    }
    else {
        // We deprecated enumNames in v5. It's intentionally omitted from RSJFSchema type, so we need to cast here.
        const schemaWithEnumNames = schema;
        const enums = schema.enum ?? [true, false];
        if (!schemaWithEnumNames.enumNames && enums.length === 2 && enums.every((v) => typeof v === 'boolean')) {
            enumOptions = [
                {
                    value: enums[0],
                    label: enums[0] ? yes : no,
                },
                {
                    value: enums[1],
                    label: enums[1] ? yes : no,
                },
            ];
        }
        else {
            enumOptions = optionsList({
                enum: enums,
                // NOTE: enumNames is deprecated, but still supported for now.
                enumNames: schemaWithEnumNames.enumNames,
            }, uiSchema);
        }
    }
    return (_jsx(Widget, { options: { ...options, enumOptions }, schema: schema, uiSchema: uiSchema, id: idSchema.$id, name: name, onChange: onChange, onFocus: onFocus, onBlur: onBlur, label: label, hideLabel: !displayLabel, value: formData, required: required, disabled: disabled, readonly: readonly, hideError: hideError, registry: registry, formContext: formContext, autofocus: autofocus, rawErrors: rawErrors }));
}
export default BooleanField;
