import Form from "react-bootstrap/Form";
import { useField } from "formik";
import AbstractField from "./AbstractField";

export default function CheckField({ title, description, fieldName, className, validate }) {
  const [field, meta] = useField({ name: fieldName, validate: validate !== undefined ? validate : (value) => {} });

  return (
    <AbstractField name={title} description={description}>
      <Form.Check {...field} aria-label="option" className={className} isInvalid={!!meta.error} />
      <Form.Control.Feedback type="invalid" style={{ display: meta.error ? "block" : "none" }}>
        {meta.error}
      </Form.Control.Feedback>
    </AbstractField>
  );
}
