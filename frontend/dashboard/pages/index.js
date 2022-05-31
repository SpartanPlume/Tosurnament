import { useEffect, useState } from "react";
import Row from "react-bootstrap/Row";
import Container from "react-bootstrap/Container";
import { useQuery } from "react-query";
import LoadingOverlay from "react-loading-overlay-ts";
import GuildCard from "../components/GuildCard";
import ErrorPage from "../components/ErrorPage";
import { queryCommonGuilds } from "../api/TosurnamentApi";

export default function Home() {
  const [guildCards, setGuildCards] = useState([]);
  const { data: guilds, isError, error, isLoading } = useQuery(queryCommonGuilds());

  useEffect(() => {
    let newGuildCards = [];
    if (guilds) {
      for (const guild of guilds) {
        //for (let i = 0; i < 10; i++) {
        newGuildCards.push(<GuildCard key={guild.id} guild={guild} />);
        //}
      }
    }
    setGuildCards(newGuildCards);
  }, [guilds]);

  if (isError) {
    return <ErrorPage error={error} />;
  }

  return (
    <Container fluid style={{ display: "flex", flexDirection: "column", padding: 0 }}>
      <LoadingOverlay active={isLoading} spinner text="Loading...">
        <Container>
          <Row xs={2} md={3} lg={4} xl={5}>
            {guildCards}
          </Row>
        </Container>
      </LoadingOverlay>
    </Container>
  );
}
