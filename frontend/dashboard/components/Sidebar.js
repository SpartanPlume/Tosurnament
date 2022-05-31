import { useEffect, useState } from "react";
import Collapse from "react-bootstrap/Collapse";
import { Drawer } from "react-bootstrap-drawer";

export default function Sidebar(props) {
  const [open, setOpen] = useState(false);
  const [drawerItems, setDrawerItems] = useState([]);
  const handleToggle = () => setOpen(!open);

  useEffect(() => {
    let newDrawerItems = [];
    for (const [index, [anchorId, anchorName, anchorIndent]] of props.anchors.entries()) {
      newDrawerItems.push(
        <Drawer.Item key={anchorId} href={`#${anchorId}`}>
          {anchorName}
          <style jsx global>{`
            .react-bootstrap-drawer-toc > div > div:nth-child(${index + 1}) > a {
              padding-left: ${anchorIndent}rem;
            }
          `}</style>
        </Drawer.Item>
      );
    }
    setDrawerItems(newDrawerItems);
  }, [props.anchors]);

  return (
    <Drawer {...props}>
      <Drawer.Toggle onClick={handleToggle} />
      <Collapse in={open}>
        <Drawer.Overflow>
          <Drawer.ToC>
            <Drawer.Nav>{drawerItems}</Drawer.Nav>
          </Drawer.ToC>
        </Drawer.Overflow>
      </Collapse>
    </Drawer>
  );
}
