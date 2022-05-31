import TextField from "./fields/TextField";
import AbstractCreateSection from "./AbstractCreateSection";

const BRACKET_FIELDS = {
  name: [TextField, { title: "Bracket name", minLength: 1, maxLength: 128, autoFocus: true }]
};

export default function CreateBracketSection(props) {
  const { tournamentId } = props;
  if (!tournamentId) {
    return <></>;
  }

  let data = Object.keys(BRACKET_FIELDS).reduce((previousValue, currentValue) => {
    previousValue[currentValue] = "";
    return previousValue;
  }, {});
  data["tournament_id"] = tournamentId;

  return (
    <AbstractCreateSection
      {...props}
      url={`/tosurnament/tournaments/${tournamentId}/brackets`}
      data={data}
      fields={BRACKET_FIELDS}
      invalidateQueryKeys={"tournament"}
    />
  );
}
