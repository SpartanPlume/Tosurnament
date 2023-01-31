import { withRouter } from "next/router";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";
import { toast } from "react-toastify";
import UtcField from "../../../components/forms/fields/UtcField";
import { Formik, Form } from "formik";
import Section from "../../../components/forms/Section";
import Col from "react-bootstrap/Col";
import LoadingOverlay from "react-loading-overlay-ts";
//import CheckField from "../../../components/forms/fields/CheckField";
import { CheckField } from "tosurnament-fields";
import { queryTournament } from "../../../api/TosurnamentApi";
import { useQuery } from "react-query";

function Register({ router }) {
  const tournamentId = router.query.tournament_id;
  const { data: tournament, isLoading } = useQuery(queryTournament(tournamentId));
  return (
    <Container fluid style={{ display: "flex", flexDirection: "column", padding: 0 }}>
      <LoadingOverlay active={isLoading} spinner text="Loading...">
        <Container fluid style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
          <Col xs={12} md={9} lg={10}>
            <Container style={{ padding: "1em" }}>
              <Section name={`Register to ${tournament?.name || ""}`}>
                <Formik initialValues={{ utc: "", accept_rules: false }}>
                  {({ isSubmitting, isValid, dirty }) => (
                    <Form>
                      <UtcField
                        title="Timezone"
                        description="This is to help tournament hosts to schedule your matches at an appropriate time."
                        fieldName="utc"
                      />
                      <CheckField
                        title="I agree to respect the tournament rules (available in the forum post)"
                        fieldName="accept_rules"
                        validate={(value) => {
                          if (!value) {
                            return "Must be checked";
                          }
                        }}
                      />
                      <Button
                        variant="primary"
                        onClick={() => (isValid ? toast.success("Registered successfully") : toast.error("Error"))}
                        style={{ display: "block", margin: "0 auto" }}
                        disabled={!isValid || !dirty}
                      >
                        Register
                      </Button>
                    </Form>
                  )}
                </Formik>
              </Section>
            </Container>
          </Col>
        </Container>
      </LoadingOverlay>
    </Container>
  );
}

export default withRouter(Register);
