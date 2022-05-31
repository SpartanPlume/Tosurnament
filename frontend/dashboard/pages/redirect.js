import { useEffect } from "react";
import { useRouter } from "next/router";
import Container from "react-bootstrap/Container";
import Cookies from "js-cookie";
import TosurnamentApi from "../api/TosurnamentApi";
import { useQueryClient } from "react-query";

export default function Redirect() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { code } = router.query;

  useEffect(() => {
    async function postToken() {
      if (!code) {
        return;
      }
      try {
        const { data } = await TosurnamentApi.post("/tosurnament/token", { code: code });
        Cookies.set("session_token", data.session_token, {
          path: "/",
          expires: 30, // Expires after 1 month
          sameSite: "strict"
        });
        queryClient.invalidateQueries("me");
        const redirectToPath = sessionStorage.getItem("redirect_after_login") || "/";
        sessionStorage.removeItem("redirect_after_login");
        router.push(redirectToPath);
      } catch (e) {
        const redirectToPath = sessionStorage.getItem("redirect_after_login") || "/";
        router.push(`/login?redirect=${redirectToPath}`);
      }
    }
    postToken();
  }, [code]);

  return (
    <Container fluid style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
      <span>Loading...</span>
    </Container>
  );
}
