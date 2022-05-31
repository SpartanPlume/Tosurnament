import Form from "react-bootstrap/Form";
import { useField } from "formik";
import AbstractField from "../AbstractField";

export default function RoleField({ title, description, fieldName, discordChannels, className }) {
  const [field] = useField(fieldName);

  let optionGroups = [];
  let parentChannelToChildren = {};
  if (discordChannels) {
    for (const channel of discordChannels) {
      if (channel.type === 0) {
        const channelParentId = channel.parent_id || "0";
        if (channelParentId in parentChannelToChildren) {
          if ("children" in parentChannelToChildren[channelParentId]) {
            parentChannelToChildren[channelParentId].children.push([channel.id, channel.name]);
          } else {
            parentChannelToChildren[channelParentId].children = [[channel.id, channel.name]];
          }
        } else {
          parentChannelToChildren[channelParentId] = { children: [[channel.id, channel.name]] };
        }
      } else if (channel.type === 4) {
        if (channel.id in parentChannelToChildren) {
          parentChannelToChildren[channel.id].name = channel.name;
        } else {
          parentChannelToChildren[channel.id] = { name: channel.name };
        }
      }
    }
  }
  for (const [parentChannelId, parentChannelInfo] of Object.entries(parentChannelToChildren)) {
    const parentChannelName = parentChannelInfo.name || "No parent";
    if ("children" in parentChannelInfo) {
      let options = [];
      for (const [channelId, channelName] of parentChannelInfo.children) {
        options.push(
          <option key={channelId} value={channelId}>
            #{channelName}
          </option>
        );
      }
      optionGroups.push(
        <optgroup key={parentChannelId} label={parentChannelName}>
          {options}
        </optgroup>
      );
    }
  }

  return (
    <AbstractField name={title} description={description}>
      <Form.Select {...field} className={className}>
        <option key="0" value="">
          No channel set
        </option>
        {optionGroups}
      </Form.Select>
    </AbstractField>
  );
}
