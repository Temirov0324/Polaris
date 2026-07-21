function drawProgressRing(canvas, percent, options = {}) {
  const ctx = canvas.getContext("2d");
  const size = canvas.width;
  const center = size / 2;
  const lineWidth = options.lineWidth || 14;
  const radius = center - lineWidth / 2;
  const clamped = Math.max(0, Math.min(100, Number(percent) || 0));

  ctx.clearRect(0, 0, size, size);

  ctx.beginPath();
  ctx.arc(center, center, radius, 0, Math.PI * 2);
  ctx.strokeStyle = options.trackColor || "#263449";
  ctx.lineWidth = lineWidth;
  ctx.stroke();

  if (clamped > 0) {
    ctx.beginPath();
    ctx.arc(center, center, radius, -Math.PI / 2, -Math.PI / 2 + (Math.PI * 2 * clamped) / 100);
    ctx.strokeStyle = options.color || "#3b82f6";
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.stroke();
  }
}

window.drawProgressRing = drawProgressRing;
