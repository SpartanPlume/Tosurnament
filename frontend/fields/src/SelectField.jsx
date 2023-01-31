import Form from "react-bootstrap/Form";
import { useField } from "formik";
import { AbstractField } from "./AbstractField";

export function SelectField({ title, description, fieldName, values, className }) {
  const [field] = useField(fieldName);

  let options = [];
  for (const [index, value] of values.entries()) {
    options.push(
      <option key={index} value={index}>
        {value}
      </option>
    );
  }

  return (
    <AbstractField name={title} description={description}>
      <Form.Select {...field} className={className}>
        {options}
      </Form.Select>
    </AbstractField>
  );
}
