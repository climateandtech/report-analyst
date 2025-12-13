import ArrayFieldDescriptionTemplate from './ArrayFieldDescriptionTemplate.js';
import ArrayFieldItemTemplate from './ArrayFieldItemTemplate.js';
import ArrayFieldTemplate from './ArrayFieldTemplate.js';
import ArrayFieldTitleTemplate from './ArrayFieldTitleTemplate.js';
import BaseInputTemplate from './BaseInputTemplate.js';
import ButtonTemplates from './ButtonTemplates/index.js';
import DescriptionField from './DescriptionField.js';
import ErrorList from './ErrorList.js';
import FieldTemplate from './FieldTemplate/index.js';
import FieldErrorTemplate from './FieldErrorTemplate.js';
import FieldHelpTemplate from './FieldHelpTemplate.js';
import ObjectFieldTemplate from './ObjectFieldTemplate.js';
import TitleField from './TitleField.js';
import UnsupportedField from './UnsupportedField.js';
import WrapIfAdditionalTemplate from './WrapIfAdditionalTemplate.js';
function templates() {
    return {
        ArrayFieldDescriptionTemplate,
        ArrayFieldItemTemplate,
        ArrayFieldTemplate,
        ArrayFieldTitleTemplate,
        ButtonTemplates: ButtonTemplates(),
        BaseInputTemplate,
        DescriptionFieldTemplate: DescriptionField,
        ErrorListTemplate: ErrorList,
        FieldTemplate,
        FieldErrorTemplate,
        FieldHelpTemplate,
        ObjectFieldTemplate,
        TitleFieldTemplate: TitleField,
        UnsupportedFieldTemplate: UnsupportedField,
        WrapIfAdditionalTemplate,
    };
}
export default templates;
