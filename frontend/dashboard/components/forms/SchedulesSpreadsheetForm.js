import TextField from "./fields/TextField";
import RangeField from "./fields/RangeField";
import IntField from "./fields/IntField";
import AbstractForm from "./AbstractForm";
import CheckField from "./fields/CheckField";

const SCHEDULES_SPREADSHEET_FIELDS = {
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
  range_match_id: [RangeField, { title: "Range match id" }],
  range_team1: [RangeField, { title: "Range team 1" }],
  range_team2: [RangeField, { title: "Range team 2" }],
  range_date: [RangeField, { title: "Range date" }],
  range_time: [RangeField, { title: "Range time" }],
  range_referee: [RangeField, { title: "Range referee" }],
  range_streamer: [RangeField, { title: "Range streamer" }],
  range_commentator: [RangeField, { title: "Range commentator" }],
  use_range: [CheckField, { title: "Store staff in multiple cells" }],
  max_referee: [IntField, { title: "Max referee in cell", min: 1, max: 3 }],
  max_streamer: [IntField, { title: "Max streamer in cell", min: 1, max: 3 }],
  max_commentator: [IntField, { title: "Max commentator in cell", min: 1, max: 4 }]
};

export default function SchedulesSpreadsheetForm(props) {
  const { tournamentId, bracketId, schedulesSpreadsheet } = props;
  return (
    <AbstractForm
      {...props}
      name={"Schedules Spreadsheet"}
      url={`/tosurnament/tournaments/${tournamentId}/brackets/${bracketId}/schedules_spreadsheet/${schedulesSpreadsheet.id}`}
      data={schedulesSpreadsheet}
      fields={SCHEDULES_SPREADSHEET_FIELDS}
      invalidateQueryKeys={"tournament"}
      withDelete
    />
  );
}
