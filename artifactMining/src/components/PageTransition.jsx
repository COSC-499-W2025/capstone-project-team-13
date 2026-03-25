import { useLocation } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import "./PageTransition.css";

export default function PageTransition({ children }) {
  const location = useLocation();
  const [displayChildren, setDisplayChildren] = useState(children);
  const [phase, setPhase] = useState("idle"); // idle | out | in
  const prevKey = useRef(location.key);

  useEffect(() => {
    if (location.key === prevKey.current) return;
    prevKey.current = location.key;

    setPhase("out");
    const t = setTimeout(() => {
      setDisplayChildren(children);
      setPhase("in");
      const t2 = setTimeout(() => setPhase("idle"), 280);
      return () => clearTimeout(t2);
    }, 140);
    return () => clearTimeout(t);
  }, [location.key, children]);

  return (
    <div className={`page-transition page-transition-${phase}`}>
      {displayChildren}
    </div>
  );
}
