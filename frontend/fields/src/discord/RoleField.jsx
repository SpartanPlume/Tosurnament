import { useEffect, useState } from "react";
import Form from "react-bootstrap/Form";
import { useField } from "formik";
import { AbstractField } from "../AbstractField";

export function RoleField({ title, description, fieldName, discordRoles, className }) {
  const [field] = useField(fieldName);
  const [selectStyle, setSelectStyle] = useState({ color: "none" });

  let options = [];
  let optionColors = [];
  const defaultColor = "#ddd";
  if (discordRoles) {
    for (const role of discordRoles) {
      const roleColor = role.color.toString(16);
      const optionColor = roleColor === "0" ? defaultColor : "#" + roleColor;
      options.push(
        <option key={role.id} value={role.id} style={{ color: optionColor }}>
          {role.name}
        </option>
      );
      optionColors[role.id] = optionColor;
    }
  }

  useEffect(() => {
    setSelectStyle({ color: optionColors[field.value] || defaultColor });
  }, [field.value, discordRoles]);

  return (
    <AbstractField name={title} description={description}>
      <Form.Select {...field} className={className} style={selectStyle}>
        <option key="0" value="" style={{ color: defaultColor }}>
          No role set
        </option>
        {options}
      </Form.Select>
    </AbstractField>
  );
}
