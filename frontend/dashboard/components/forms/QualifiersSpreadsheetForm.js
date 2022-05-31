import TextField from "./fields/TextField";
import RangeField from "./fields/RangeField";
import IntField from "./fields/IntField";
import AbstractForm from "./AbstractForm";

const QUALIFIERS_SPREADSHEET_FIELDS = {
  spreadsheet_id: [TextField, { title: "Spreadsheet URL or id", minLength: 1, maxLength: 128 }],
  sheet_name: [
    TextField,
    {
      title: "Sheet name",
      description: "Used in all the ranges of the spreadsheet (unless explicitly set in the range)",
      minLength: 0,
      maxLength: 128
    }
  ],
  range_lobby_id: [RangeField, { title: "Range lobby id" }],
  range_teams: [RangeField, { title: "Range teams" }],
  range_referee: [RangeField, { title: "Range referee" }],
  range_date: [RangeField, { title: "Range date" }],
  range_time: [RangeField, { title: "Range time" }],
  max_teams_in_row: [
    IntField,
    {
      title: "Max teams in row",
      description: "Specify how many teams can be present in one row of a lobby.",
      min: 0,
      max: 128
    }
  ]
};

export default function QualifiersSpreadsheetForm(props) {
  const { tournamentId, bracketId, qualifiersSpreadsheet } = props;
  return (
    <AbstractForm
      {...props}
      name={"Qualifiers Spreadsheet"}
      url={`/tosurnament/tournaments/${tournamentId}/brackets/${bracketId}/qualifiers_spreadsheet/${qualifiersSpreadsheet.id}`}
      data={qualifiersSpreadsheet}
      fields={QUALIFIERS_SPREADSHEET_FIELDS}
      invalidateQueryKeys={"tournament"}
      withDelete
    />
  );
}
