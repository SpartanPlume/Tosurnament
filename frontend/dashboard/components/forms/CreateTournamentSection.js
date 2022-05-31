import TextField from "./fields/TextField";
import AbstractCreateSection from "./AbstractCreateSection";

const TOURNAMENT_FIELDS = {
  name: [TextField, { title: "Tournament name", minLength: 1, maxLength: 128, autoFocus: true }],
  acronym: [TextField, { title: "Acronym", minLength: 1, maxLength: 16 }]
};

export default function CreateTournamentSection(props) {
  const { guildId } = props;
  if (!guildId) {
    return <></>;
  }

  let data = Object.keys(TOURNAMENT_FIELDS).reduce((previousValue, currentValue) => {
    previousValue[currentValue] = "";
    return previousValue;
  }, {});
  data["guild_id"] = guildId;

  return (
    <AbstractCreateSection
      {...props}
      url={"/tosurnament/tournaments"}
      data={data}
      fields={TOURNAMENT_FIELDS}
      invalidateQueryKeys={"tournament"}
    />
  );
}
