import Form from "react-bootstrap/Form";
import Tooltip from "./Tooltip";

export default function AbstractField(props) {
  const { name, description, children } = props;
  return (
    <Form.Group {...props} className="mb-3">
      <Form.Label>{name}:</Form.Label>
      <Tooltip description={description} />
      {children}
    </Form.Group>
  );
}
