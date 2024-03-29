import { useEffect } from "react";
import { useRouter } from "next/router";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";

export default function Login() {
  const router = useRouter();
  const { redirect } = router.query;

  useEffect(() => {
    const redirectToPath = redirect || "/";
    sessionStorage.setItem("redirect_after_login", redirectToPath);
  }, [redirect]);

  const encodedRedirectUriPath = encodeURI(process.env.NEXT_PUBLIC_DISCORD_REDIRECT_URI);

  return (
    <Container fluid style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
      <Button
        variant="primary"
        onClick={() =>
          (window.location = `https://discord.com/api/v9/oauth2/authorize?client_id=378433574602539019&redirect_uri=${encodedRedirectUriPath}&response_type=code&scope=guilds%20identify`)
        }
        style={{ display: "block", margin: "0 auto" }}
      >
        Login with Discord
      </Button>
    </Container>
  );
}
