import React from "react";
import TextField from "./fields/TextField";
import RoleField from "./fields/discord/RoleField";
import AbstractForm from "./AbstractForm";

const GUILD_FIELDS = {
  language: [
    TextField,
    { title: "Language", description: "Language used by the discord bot.", minLength: 0, maxLength: 8 }
  ],
  admin_role_id: [
    RoleField,
    {
      title: "Admin role",
      description:
        "Everyone with this role can modify the bot settings and has some privileged rights on some commands."
    }
  ],
  verified_role_id: [
    RoleField,
    { title: "Verified role", description: "Role that will be given when a user gets verified." }
  ]
};

export default function GuildForm(props) {
  const { guild } = props;
  if (!guild) {
    return <></>;
  }

  return (
    <AbstractForm
      {...props}
      name={"Guild"}
      url={`/tosurnament/guilds/${guild.id}`}
      data={guild}
      fields={GUILD_FIELDS}
      invalidateQueryKeys={["guild", { guild_id: guild.guild_id_snowflake }]}
    />
  );
}
