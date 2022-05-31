import { useEffect, useState } from "react";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import InputGroup from "react-bootstrap/InputGroup";
import { useField } from "formik";
import AbstractField from "./AbstractField";

export default function UtcField({ title, description, fieldName, className }) {
  const [field, meta, helpers] = useField(fieldName);
  const [selectValue, setSelectValue] = useState("+");
  const [timeValue, setTimeValue] = useState("00:00");
  const [hasBeenUpdated, setHasBeenUpdated] = useState(false);
  useEffect(() => {
    if (field.value && field.value !== "") {
      const operator = field.value.charAt(0);
      const time = field.value.substring(1);
      setSelectValue(operator);
      setTimeValue(time || "");
    }
  }, [field.value]);

  useEffect(() => {
    if (hasBeenUpdated) {
      let utcFieldValue = "";
      if (timeValue && timeValue !== "") {
        utcFieldValue = selectValue + timeValue;
      }
      helpers.setValue(utcFieldValue);
    }
  }, [selectValue, timeValue]);

  const onSelectChange = (e) => {
    setHasBeenUpdated(true);
    setSelectValue(e.target.value);
  };

  const onTimeChange = (e) => {
    setHasBeenUpdated(true);
    setTimeValue(e.target.value);
  };

  return (
    <AbstractField name={title} description={description}>
      <InputGroup>
        <Col xs={2} lg={1}>
          <Form.Select value={selectValue} onChange={onSelectChange}>
            <option key="+" value="+">
              +
            </option>
            <option key="-" value="-">
              -
            </option>
          </Form.Select>
        </Col>
        <Col>
          <Form.Control className={className} type="time" value={timeValue} onChange={onTimeChange} />
        </Col>
      </InputGroup>
    </AbstractField>
  );
}
