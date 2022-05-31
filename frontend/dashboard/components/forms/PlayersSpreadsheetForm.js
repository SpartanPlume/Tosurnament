import TextField from "./fields/TextField";
import RangeField from "./fields/RangeField";
import IntField from "./fields/IntField";
import AbstractForm from "./AbstractForm";

const PLAYERS_SPREADSHEET_FIELDS = {
  spreadsheet_id: [TextField, { title: "Spreadsheet URL or id", minLength: 1, maxLength: 128 }],
  sheet_name: [
    TextField,
    {
      title: "Sheet name",
      description: "Used in all the ranges of the spreadsheet (unless explicitly set in the range).",
      minLength: 0,
      maxLength: 128
    }
  ],
  range_team_name: [RangeField, { title: "Range team name" }],
  range_team: [RangeField, { title: "Range team" }],
  range_discord_id: [RangeField, { title: "Range discord id" }],
  range_discord: [
    RangeField,
    {
      title: "Range discord",
      description: "Range that will contain the discord username and discriminant like this Username#0000."
    }
  ],
  range_rank: [RangeField, { title: "Range rank" }],
  range_osu_id: [RangeField, { title: "Range osu id" }],
  range_pp: [RangeField, { title: "Range pp" }],
  range_country: [RangeField, { title: "Range country" }],
  range_timezone: [
    RangeField,
    { title: "Range timezone", description: "Range that will contain the timezone given during registration." }
  ],
  max_range_for_teams: [
    IntField,
    {
      title: "Max range for teams",
      description: "Specify how many cells in a line contains a team. To use when storing multiple teams on a line.",
      min: 0,
      max: 128
    }
  ]
};

export default function PlayersSpreadsheetForm(props) {
  const { tournamentId, bracketId, playersSpreadsheet } = props;
  return (
    <AbstractForm
      {...props}
      name={"Players Spreadsheet"}
      url={`/tosurnament/tournaments/${tournamentId}/brackets/${bracketId}/players_spreadsheet/${playersSpreadsheet.id}`}
      data={playersSpreadsheet}
      fields={PLAYERS_SPREADSHEET_FIELDS}
      invalidateQueryKeys={"tournament"}
      withDelete
    />
  );
}
