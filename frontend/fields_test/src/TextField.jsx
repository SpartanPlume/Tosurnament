import { useEffect, useState } from "react";
import Form from "react-bootstrap/Form";
import { useField } from "formik";
import { AbstractField } from "./AbstractField";

export function TextField({ title, description, fieldName, minLength, maxLength, className, onKeyPress, autoFocus }) {
  const [inputRef, setInputRef] = useState(null);
  const [field, meta] = useField({
    name: fieldName,
    validate: (value) => {
      const valueLength = value?.length || 0;
      if (minLength && valueLength < minLength) {
        return `Field must contain ${minLength} characters or more`;
      } else if (maxLength && valueLength > maxLength) {
        return `Field must contain ${maxLength} characters or less`;
      }
    }
  });

  useEffect(() => {
    if (autoFocus && inputRef) {
      inputRef.focus();
    }
  }, [autoFocus, inputRef]);

  return (
    <AbstractField name={title} description={description}>
      <Form.Control
        className={className}
        type="text"
        onKeyPress={onKeyPress}
        isInvalid={!!meta.error}
        ref={(ref) => setInputRef(ref)}
        {...field}
      />
      <Form.Control.Feedback type="invalid">{meta.error}</Form.Control.Feedback>
    </AbstractField>
  );
}
