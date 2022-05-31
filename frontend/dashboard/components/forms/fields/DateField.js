import { useEffect, useState } from "react";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import { useField } from "formik";
import AbstractField from "./AbstractField";

export default function DateField({ title, description, fieldName, className }) {
  const daysOfWeek = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
  const [field, meta, helpers] = useField(fieldName);
  const [selectValue, setSelectValue] = useState("Not set");
  const [timeValue, setTimeValue] = useState("");
  useEffect(() => {
    const [day, time] = field.value?.split(" ") || ["", ""];
    setSelectValue(day || "Not set");
    setTimeValue(time || "00:00");
  }, [field.value]);

  useEffect(() => {
    let dateFieldValue = "";
    if (selectValue !== "Not set") {
      dateFieldValue = selectValue + " " + timeValue;
    }
    helpers.setValue(dateFieldValue);
  }, [selectValue, timeValue]);

  let options = [];
  for (const dayName of daysOfWeek) {
    options.push(
      <option key={dayName} value={dayName}>
        {dayName}
      </option>
    );
  }

  const onSelectChange = (e) => {
    setSelectValue(e.target.value);
  };

  const onTimeChange = (e) => {
    setTimeValue(e.target.value);
  };

  return (
    <AbstractField name={title} description={description}>
      <Row>
        <Col>
          <Form.Select className={className} value={selectValue} onChange={onSelectChange}>
            <option key="Not set" value="Not set">
              Not set
            </option>
            {options}
          </Form.Select>
        </Col>
        <Col>
          <Form.Control
            className={className}
            type="time"
            value={timeValue}
            onChange={onTimeChange}
            disabled={selectValue === "Not set"}
          />
        </Col>
      </Row>
    </AbstractField>
  );
}
