function drawBarChart(canvas, data, options = {}) {
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 22;

  ctx.clearRect(0, 0, width, height);

  const max = Math.max(1, ...data.map((d) => d.value));
  const barSlot = width / data.length;

  data.forEach((d, i) => {
    const barHeight = ((height - padding) * d.value) / max;
    const barW = barSlot * 0.5;
    const x = i * barSlot + (barSlot - barW) / 2;
    const y = height - padding - barHeight;
    const radius = Math.min(4, barW / 2);

    ctx.fillStyle = d.value > 0 ? options.color || "#3b82f6" : "#263449";
    ctx.beginPath();
    ctx.moveTo(x, y + barHeight);
    ctx.lineTo(x, y + radius);
    ctx.arcTo(x, y, x + radius, y, radius);
    ctx.lineTo(x + barW - radius, y);
    ctx.arcTo(x + barW, y, x + barW, y + radius, radius);
    ctx.lineTo(x + barW, y + barHeight);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = options.labelColor || "#8f9cb3";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(d.label, x + barW / 2, height - 6);
  });
}

window.drawBarChart = drawBarChart;
