import Form from "react-bootstrap/Form";
import { useField } from "formik";
import AbstractField from "./AbstractField";

export default function CheckField({ title, description, fieldName, className }) {
  const [field] = useField(fieldName);

  return (
    <AbstractField name={title} description={description}>
      <Form.Check {...field} aria-label="option" className={className} />
    </AbstractField>
  );
}
