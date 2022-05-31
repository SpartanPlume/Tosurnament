import Form from "react-bootstrap/Form";
import { useField } from "formik";
import AbstractField from "./AbstractField";

export default function IntField({ title, description, fieldName, min, max, className }) {
  const [field, meta] = useField({
    name: fieldName,
    validate: (value) => {
      if (min && value < min) {
        return `Number must be ${min} or above`;
      } else if (max && value > max) {
        return `Number must be ${max} or below`;
      } else if (!value && value !== 0) {
        return "Must be a number";
      }
    }
  });

  return (
    <AbstractField name={title} description={description}>
      <Form.Control {...field} className={className} type="number" min={min} max={max} isInvalid={!!meta.error} />
      <Form.Control.Feedback type="invalid">{meta.error}</Form.Control.Feedback>
    </AbstractField>
  );
}
