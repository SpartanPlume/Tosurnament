import Container from "react-bootstrap/Container";

export default function ErrorPage({ error }) {
  if (!error) {
    return;
  }

  const ERROR_STATUS_TO_MESSAGE = {
    401: "You need to be authenticated to be able to access this page.",
    403: "You do not have the required permissions to access this page.",
    404: "Page not found."
  };

  const message =
    error.response.status in ERROR_STATUS_TO_MESSAGE
      ? ERROR_STATUS_TO_MESSAGE[error.response.status]
      : "An unexpected error occurred. Please retry.";

  return (
    <Container fluid style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
      <div>{message}</div>
    </Container>
  );
}
