import React from "react";
import TextField from "./fields/TextField";
import AbstractCreateSection from "./AbstractCreateSection";

const SPREADSHEET_FIELDS = {
  spreadsheet_id: [TextField, { title: "Spreadsheet URL or id", minLength: 1, maxLength: 128, autoFocus: true }],
  sheet_name: [
    TextField,
    {
      title: "Sheet name",
      description: "Used in all the ranges of the spreadsheet (unless explicitly set in the range).",
      minLength: 0,
      maxLength: 128
    }
  ]
};

export default function CreateSpreadsheetSection(props) {
  let data = Object.keys(SPREADSHEET_FIELDS).reduce((previousValue, currentValue) => {
    previousValue[currentValue] = "";
    return previousValue;
  }, {});

  return (
    <AbstractCreateSection {...props} data={data} fields={SPREADSHEET_FIELDS} invalidateQueryKeys={"tournament"} />
  );
}
