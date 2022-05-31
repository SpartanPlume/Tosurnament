import TextField from "./fields/TextField";
import RoleField from "./fields/discord/RoleField";
import AbstractForm from "./AbstractForm";

const BRACKET_FIELDS = {
  name: [TextField, { title: "Name", minLength: 1, maxLength: 128 }],
  role_id: [
    RoleField,
    {
      title: "Role",
      description:
        "This role can be given automatically during the registration phase and removed when the player is out of the tournament."
    }
  ],
  challonge: [
    TextField,
    {
      title: "Challonge",
      description:
        "URL of the challonge. It can be automatically updated when using the result posting of Tosurnament.",
      minLength: 0,
      maxLength: 128
    }
  ]
};

export default function BracketForm(props) {
  let bracket = Object.assign({}, props.bracket);
  delete bracket.players_spreadsheet;
  delete bracket.schedules_spreadsheet;
  delete bracket.qualifiers_spreadsheet;
  delete bracket.qualifiers_results_spreadsheet;

  return (
    <AbstractForm
      {...props}
      name={`Bracket: ${bracket.name}`}
      url={`/tosurnament/tournaments/${props.tournamentId}/brackets/${bracket.id}`}
      data={bracket}
      fields={BRACKET_FIELDS}
      invalidateQueryKeys={"tournament"}
      withDelete
    />
  );
}
