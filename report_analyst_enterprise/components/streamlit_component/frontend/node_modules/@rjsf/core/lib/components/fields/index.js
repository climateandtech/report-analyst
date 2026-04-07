import ArrayField from './ArrayField.js';
import BooleanField from './BooleanField.js';
import MultiSchemaField from './MultiSchemaField.js';
import NumberField from './NumberField.js';
import ObjectField from './ObjectField.js';
import SchemaField from './SchemaField.js';
import StringField from './StringField.js';
import NullField from './NullField.js';
function fields() {
    return {
        AnyOfField: MultiSchemaField,
        ArrayField: ArrayField,
        // ArrayField falls back to SchemaField if ArraySchemaField is not defined, which it isn't by default
        BooleanField,
        NumberField,
        ObjectField,
        OneOfField: MultiSchemaField,
        SchemaField,
        StringField,
        NullField,
    };
}
export default fields;
