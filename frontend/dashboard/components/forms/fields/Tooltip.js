import { useEffect, useState } from "react";
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Popover from "react-bootstrap/Popover";

export default function Tooltip({ description }) {
  const [show, setShow] = useState(false);

  if (!description) {
    return;
  }

  const popover = (
    <Popover>
      <Popover.Body>{description}</Popover.Body>
    </Popover>
  );

  useEffect(() => {
    window.addEventListener("scroll", () => {
      setShow(false);
    });
  }, []);

  return (
    <OverlayTrigger
      id="test"
      trigger="click"
      placement="right"
      overlay={popover}
      rootClose
      show={show}
      onToggle={(nextShow) => setShow(nextShow)}
      onHide={() => setShow(false)}
    >
      <div className="field-tooltip">
        <span className="field-tooltip-text">?</span>
        <style global jsx>{`
          .field-tooltip {
            width: 1.25em;
            height: 1.25em;
            border-radius: 50%;
            border-style: solid;
            border-width: 1px;
            display: inline-block;
            text-align: center;
            margin-left: 0.5em;
            font-size: 0.8em;
          }

          .field-tooltip:hover {
            cursor: pointer;
          }

          .field-tooltip-text {
            position: relative;
            top: -0.25em;
            user-select: none;
          }
        `}</style>
      </div>
    </OverlayTrigger>
  );
}
