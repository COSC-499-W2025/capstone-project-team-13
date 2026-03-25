import { useEffect, useState } from "react";
import "./LoadingBar.css";

// Event bus
let _count = 0;
const _subs = new Set();
function notify() { _subs.forEach(fn => fn(_count)); }

export const loadingBar = {
  start() { _count++; notify(); },
  done()  { _count = Math.max(0, _count - 1); notify(); },
};

export default function LoadingBar() {
  const [active, setActive] = useState(false);
  const [width, setWidth]   = useState(0);
  const [fading, setFading] = useState(false);
  const timerRef = { t: null };

  useEffect(() => {
    let growing;
    function handler(count) {
      if (count > 0) {
        setFading(false);
        setActive(true);
        setWidth(30);
        clearInterval(growing);
        growing = setInterval(() => {
          setWidth(w => w < 85 ? w + (85 - w) * 0.06 : w);
        }, 120);
      } else {
        clearInterval(growing);
        setWidth(100);
        setTimeout(() => {
          setFading(true);
          setTimeout(() => { setActive(false); setWidth(0); setFading(false); }, 380);
        }, 180);
      }
    }
    _subs.add(handler);
    return () => { _subs.delete(handler); clearInterval(growing); };
  }, []);

  if (!active) return null;
  return (
    <div className={`loading-bar-track ${fading ? "loading-bar-fade" : ""}`}>
      <div className="loading-bar-fill" style={{ width: `${width}%` }} />
    </div>
  );
}
