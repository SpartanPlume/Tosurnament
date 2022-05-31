import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Cookies from "js-cookie";
import Nav from "react-bootstrap/Nav";
import NavItem from "react-bootstrap/NavItem";
import NavLink from "react-bootstrap/NavLink";
import Navbar from "react-bootstrap/Navbar";
import Dropdown from "react-bootstrap/Dropdown";
import Container from "react-bootstrap/Container";
import Image from "react-bootstrap/Image";
import TosurnamentApi, { queryMe } from "../api/TosurnamentApi";
import { useQuery, useQueryClient } from "react-query";

export default function Header() {
  const { data: user, isError, error } = useQuery(queryMe());
  const queryClient = useQueryClient();
  const [userDropdown, setUserDropdown] = useState();
  const router = useRouter();

  useEffect(() => {
    const userToUse = user || JSON.parse(localStorage.getItem("user"));
    if (userToUse && (!isError || error?.response?.status !== 401)) {
      setUserDropdown(
        <Dropdown as={NavItem}>
          <Dropdown.Toggle as={NavLink} className="header-text">
            <Image
              roundedCircle
              src={`https://cdn.discordapp.com/avatars/${userToUse.id}/${userToUse.avatar}.png?size=32`}
              style={{ marginRight: "0.5em" }}
            />
            {userToUse.username}
          </Dropdown.Toggle>
          <Dropdown.Menu>
            <Dropdown.Item onClick={logout}>Logout</Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
      );
    } else {
      localStorage.removeItem("user");
      setUserDropdown(<Nav.Link href="/login">Login</Nav.Link>);
    }
    if (user) {
      localStorage.setItem("user", JSON.stringify({ id: user.id, avatar: user.avatar, username: user.username }));
    }
  }, [user, isError]);

  const logout = async (e) => {
    try {
      await TosurnamentApi.post("/tosurnament/token/revoke", null);
    } catch {
      return;
    }
    localStorage.removeItem("user");
    Cookies.remove("session_token", { path: "/" });
    queryClient.invalidateQueries("me");
    router.replace("/login");
  };

  return (
    <Navbar fixed="top" bg="dark" variant="dark" className="header">
      <Container>
        <Navbar.Brand href="/" className="header-text">
          Tosurnament
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse className="justify-content-end">
          <Nav>{userDropdown}</Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}
