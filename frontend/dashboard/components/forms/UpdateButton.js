import Button from "react-bootstrap/Button";

export default function UpdateButton({ isSubmitting, disabled }) {
  return (
    <Button variant="primary" type="submit" disabled={isSubmitting || disabled} style={{ marginTop: "0.5em" }}>
      Update
    </Button>
  );
}
