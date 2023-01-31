import Form from "react-bootstrap/Form";
import { useField } from "formik";
import { AbstractField } from "./AbstractField";

export function RangeField({ title, description, fieldName, className }) {
  const rangeRegex = "([A-Z]+\\d*|\\d+)(:([A-Z]+\\d*|\\d+))?";
  const fullRegex = new RegExp("^" + rangeRegex + "((,| |, |;|; ||)" + rangeRegex + ")*$");

  const [field, meta, helpers] = useField({
    name: fieldName,
    validate: (value) => {
      const valueLength = value?.length || 0;
      if (valueLength !== 0 && !value.match(fullRegex)) {
        return "Invalid range";
      }
    }
  });

  const onTextChange = (e) => {
    helpers.setValue(e.target.value.toUpperCase());
  };

  return (
    <AbstractField name={title} description={description}>
      <Form.Control {...field} className={className} type="text" onChange={onTextChange} isInvalid={!!meta.error} />
      <Form.Control.Feedback type="invalid">{meta.error}</Form.Control.Feedback>
    </AbstractField>
  );
}
