import Link from "next/link";
import Card from "react-bootstrap/Card";
import Image from "react-bootstrap/Image";
import Col from "react-bootstrap/Col";

export default function GuildCard({ guild }) {
  let guildIcon = null;
  if (guild.icon) {
    guildIcon = <Image src={`https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png?size=256`} />;
  }
  return (
    <Col xs>
      <Link href={`/guilds/${guild.id}`}>
        <Card
          className="text-center"
          border="light"
          style={{ cursor: "pointer", padding: "0.5em 1em", margin: "1em 0.5em" }}
        >
          {guildIcon}
          <Card.Title style={{ marginTop: "1em" }}>{guild.name}</Card.Title>
        </Card>
      </Link>
    </Col>
  );
}
