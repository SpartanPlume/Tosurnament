import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Head from "next/head";
import Container from "react-bootstrap/Container";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import {
  queryGuildFromDiscordGuildId,
  queryTournamentFromDiscordGuildId,
  queryDiscordRoles,
  queryDiscordChannels
} from "../../api/TosurnamentApi";
import { withRouter } from "next/router";
import LoadingOverlay from "react-loading-overlay-ts";
import GuildForm from "../../components/forms/GuildForm";
import TournamentForm from "../../components/forms/TournamentForm";
import BracketForm from "../../components/forms/BracketForm";
import PlayersSpreadsheetForm from "../../components/forms/PlayersSpreadsheetForm";
import SchedulesSpreadsheetForm from "../../components/forms/SchedulesSpreadsheetForm";
import QualifiersSpreadsheetForm from "../../components/forms/QualifiersSpreadsheetForm";
import CreateSpreadsheetSection from "../../components/forms/CreateSpreadsheetSection";
import CreateTournamentSection from "../../components/forms/CreateTournamentSection";
import CreateBracketSection from "../../components/forms/CreateBracketSection";
import ErrorPage from "../../components/ErrorPage";
import { useQueries } from "react-query";

function GuildPage({ router }) {
  const guildId = router.query.id;
  const Sidebar = dynamic(() => import("../../components/Sidebar"), { ssr: false });
  const [forms, setForms] = useState([]);
  const [anchors, setAnchors] = useState([]);
  const results = useQueries([
    queryGuildFromDiscordGuildId(guildId),
    queryTournamentFromDiscordGuildId(guildId),
    queryDiscordRoles(guildId),
    queryDiscordChannels(guildId)
  ]);
  const isLoading = results.some((r) => r.isLoading);
  const isFetching = results.some((r) => r.isFetching);
  const errorResult = results.find((r) => r.isError);
  const guild = results[0].data;
  const tournament = results[1].data;
  const discordRoles = results[2].data;
  const discordChannels = results[3].data;

  useEffect(() => {
    if (isFetching) {
      return;
    }
    let newAnchors = [];
    newAnchors.push(["Guild", "Guild", 1]);
    newAnchors.push(["Tournament", "Tournament", 1]);

    let newForms = [];
    if (tournament) {
      newForms.push(
        <TournamentForm
          key={"Tournament"}
          id={"Tournament"}
          tournament={tournament}
          discordRoles={discordRoles}
          discordChannels={discordChannels}
        />
      );
      for (const bracket of tournament.brackets) {
        newForms.push(
          <BracketForm
            key={`${bracket.id}-Bracket`}
            id={`${bracket.id}-Bracket`}
            tournamentId={tournament.id}
            bracket={bracket}
            discordRoles={discordRoles}
            discordChannels={discordChannels}
          />
        );
        newAnchors.push([`${bracket.id}-Bracket`, `Bracket: ${bracket.name}`, 2]);

        if (bracket.players_spreadsheet) {
          newForms.push(
            <PlayersSpreadsheetForm
              key={`${bracket.id}-PlayersSpreadsheet`}
              id={`${bracket.id}-PlayersSpreadsheet`}
              tournamentId={tournament.id}
              bracketId={bracket.id}
              playersSpreadsheet={bracket.players_spreadsheet}
            />
          );
        } else {
          newForms.push(
            <CreateSpreadsheetSection
              key={`${bracket.id}-PlayersSpreadsheet`}
              id={`${bracket.id}-PlayersSpreadsheet`}
              name="Players Spreadsheet"
              url={`/tosurnament/tournaments/${tournament.id}/brackets/${bracket.id}/players_spreadsheet`}
            />
          );
        }
        newAnchors.push([`${bracket.id}-PlayersSpreadsheet`, "Players Spreadsheet", 3]);
        if (bracket.schedules_spreadsheet) {
          newForms.push(
            <SchedulesSpreadsheetForm
              key={`${bracket.id}-SchedulesSpreadsheet`}
              id={`${bracket.id}-SchedulesSpreadsheet`}
              tournamentId={tournament.id}
              bracketId={bracket.id}
              schedulesSpreadsheet={bracket.schedules_spreadsheet}
            />
          );
        } else {
          newForms.push(
            <CreateSpreadsheetSection
              key={`${bracket.id}-SchedulesSpreadsheet`}
              id={`${bracket.id}-SchedulesSpreadsheet`}
              name="Schedules Spreadsheet"
              url={`/tosurnament/tournaments/${tournament.id}/brackets/${bracket.id}/schedules_spreadsheet`}
            />
          );
        }
        newAnchors.push([`${bracket.id}-SchedulesSpreadsheet`, "Schedules Spreadsheet", 3]);
        if (bracket.qualifiers_spreadsheet) {
          newForms.push(
            <QualifiersSpreadsheetForm
              key={`${bracket.id}-QualifiersSpreadsheet`}
              id={`${bracket.id}-QualifiersSpreadsheet`}
              tournamentId={tournament?.id}
              bracketId={bracket.id}
              qualifiersSpreadsheet={bracket.qualifiers_spreadsheet}
            />
          );
        } else {
          newForms.push(
            <CreateSpreadsheetSection
              key={`${bracket.id}-QualifiersSpreadsheet`}
              id={`${bracket.id}-QualifiersSpreadsheet`}
              name="Qualifiers Spreadsheet"
              url={`/tosurnament/tournaments/${tournament.id}/brackets/${bracket.id}/qualifiers_spreadsheet`}
            />
          );
        }
        newAnchors.push([`${bracket.id}-QualifiersSpreadsheet`, "Qualifiers Spreadsheet", 3]);
      }
      newForms.push(
        <CreateBracketSection key="NewBracket" id="NewBracket" name="New Bracket" tournamentId={tournament.id} />
      );
      newAnchors.push(["NewBracket", "New Bracket", 2]);
    } else {
      newForms.push(<CreateTournamentSection key="Tournament" id="Tournament" name="Tournament" guildId={guildId} />);
    }
    setForms(newForms);
    setAnchors(newAnchors);
  }, [isFetching]);

  if (errorResult) {
    return <ErrorPage error={errorResult.error} />;
  }

  return (
    <Container fluid style={{ display: "flex", flexDirection: "column", padding: 0 }}>
      <LoadingOverlay active={isLoading} spinner text="Loading...">
        <Head>
          <title>{tournament ? tournament.name : "No tournament"}</title>
        </Head>
        <Container fluid>
          <Row className="flex-xl-nowrap">
            <Col xs={12} md={3} lg={2} style={{ padding: "0" }}>
              <Sidebar anchors={anchors} />
            </Col>
            <Col xs={12} md={9} lg={10}>
              <Container style={{ padding: "1em" }}>
                <GuildForm guild={guild} discordRoles={discordRoles} />
                {forms}
              </Container>
            </Col>
          </Row>
        </Container>
      </LoadingOverlay>
    </Container>
  );
}

export function getServerSideProps(ctx) {
  return {
    props: {}
  };
}

export default withRouter(GuildPage);
