import TextField from "./fields/TextField";
import CheckField from "./fields/CheckField";
import SelectField from "./fields/SelectField";
import IntField from "./fields/IntField";
import DateField from "./fields/DateField";
import UtcField from "./fields/UtcField";
import RoleField from "./fields/discord/RoleField";
import ChannelField from "./fields/discord/ChannelField";
import AbstractForm from "./AbstractForm";

const TOURNAMENT_FIELDS = {
  name: [TextField, { title: "Name", minLength: 1, maxLength: 128 }],
  acronym: [TextField, { title: "Acronym", minLength: 1, maxLength: 16 }],
  staff_channel_id: [ChannelField, { title: "Staff channel", description: "Used for staff notifications." }],
  match_notification_channel_id: [
    ChannelField,
    {
      title: "Match notification channel",
      description: "Used for match notifications that will happen 30 minutes before a match."
    }
  ],
  player_role_id: [RoleField, { title: "Player role" }],
  referee_role_id: [RoleField, { title: "Referee role" }],
  streamer_role_id: [RoleField, { title: "Streamer role" }],
  commentator_role_id: [RoleField, { title: "Commentator role" }],
  team_captain_role_id: [RoleField, { title: "Team Captain role" }],
  reschedule_deadline_hours_before_current_time: [
    IntField,
    {
      title: "Reschedule deadline hours before current time",
      description:
        "Allow a reschedule until <number of hours specified> before the current match time. 0 is for no deadline.",
      min: 0,
      max: 72
    }
  ],
  reschedule_deadline_hours_before_new_time: [
    IntField,
    {
      title: "Reschedule deadline hours before new time",
      description:
        "Allow a reschedule until <number of hours specified> before the new match time. 0 is for no deadline.",
      min: 0,
      max: 72
    }
  ],
  reschedule_deadline_end: [
    DateField,
    { title: "Reschedule deadline end", description: "Allow a reschedule date before the next specified day and hour." }
  ],
  reschedule_before_date: [
    DateField,
    {
      title: "Reschedule before date",
      description: "Allow a reschedule date after the previous specified day and hour."
    }
  ],
  reschedule_ping_team: [
    CheckField,
    {
      title: "Reschedule ping team",
      description: "When checked, reschedules will ping the team role. Else, reschedules will ping the Team Captain."
    }
  ],
  notify_no_staff_reschedule: [
    CheckField,
    {
      title: "Notify no staff reschedule",
      description:
        "When checked, reschedules of matches that no staff took yet will be notified in the staff channel. Else, they will not be notified."
    }
  ],
  game_mode: [SelectField, { title: "Game mode", values: ["std", "taiko", "ctb", "mania"] }],
  utc: [UtcField, { title: "UTC", description: "Used in all written dates by the discord bot." }]
};

export default function TournamentForm(props) {
  let tournament = Object.assign({}, props.tournament);
  delete tournament.brackets;

  return (
    <AbstractForm
      {...props}
      name={"Tournament"}
      url={`/tosurnament/tournaments/${tournament.id}`}
      data={tournament}
      fields={TOURNAMENT_FIELDS}
      invalidateQueryKeys={["tournament", { guild_id: tournament.guild_id_snowflake }]}
      withDelete
    />
  );
}
