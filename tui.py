import traceback
import time
import locale
from collections import deque
from typing import Dict, Any, List

try:
    import curses
except ImportError:
    curses = None

import tests.cpu_test as cpu_test
import tests.disks_test as disks_test
import tests.gpu_test as gpu_test
import tests.network_test as network_test
import tests.usb_test as usb_test
import core.report as report_gen
from core.system_monitor import RealtimeMonitor, human_bytes


def _run_cpu() -> Dict[str, Any]:
    res = cpu_test.cpu_test()
    return {"component": "CPU", "status": _map_status(res.status.value), "message": res.message, "data": res.data}


def _run_disks() -> Dict[str, Any]:
    res = disks_test.disks_test()
    return {"component": "Disks", "status": _map_status(res.status.value), "message": res.message, "data": res.data}


def _run_gpu() -> Dict[str, Any]:
    res = gpu_test.gpu_test()
    return {"component": "GPU", "status": _map_status(res.status.value), "message": res.message, "data": res.data}


def _run_network() -> Dict[str, Any]:
    res = network_test.network_test()
    return {"component": "Network", "status": _map_status(res.status.value), "message": res.message, "data": res.data}


def _run_usb() -> Dict[str, Any]:
    res = usb_test.usb_test()
    return {"component": "USB", "status": _map_status(res.status.value), "message": res.message, "data": res.data}


def _map_status(status: str) -> str:
    if status == "FAIL":
        return "error"
    if status == "WARN":
        return "warning"
    return "ok"


def _wrap_text(text: str, width: int) -> List[str]:
    if width <= 0:
        return [text]

    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        proposal = f"{current} {word}"
        if len(proposal) <= width:
            current = proposal
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


class DiagnosticTUI:
    def __init__(self):
        self.menu_items = [
            "Run CPU Test",
            "Run Disks Test",
            "Run GPU Test",
            "Run Network Test",
            "Run USB Test",
            "Realtime Monitor",
            "Run All Tests",
            "Save Report",
            "Clear Results",
            "Quit",
        ]
        self.selected = 0
        self.results: List[Dict[str, Any]] = []
        self.last_message = "Ready"
        self.monitor = RealtimeMonitor()
        self.cpu_history = deque(maxlen=72)
        self.mem_history = deque(maxlen=72)
        self.net_history = deque(maxlen=72)
        self.swap_history = deque(maxlen=72)
        self.disk_history = deque(maxlen=72)
        self._colors_enabled = False
        self.monitor_focus = "cpu"
        self._unicode_graph = self._detect_unicode_graph_support()

    @staticmethod
    def _detect_unicode_graph_support() -> bool:
        enc = (locale.getpreferredencoding(False) or "").lower()
        return "utf" in enc

    def _init_colors(self):
        if not curses or self._colors_enabled:
            return
        if not curses.has_colors():
            return

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)    # title/info
        curses.init_pair(2, curses.COLOR_GREEN, -1)   # healthy
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # warning
        curses.init_pair(4, curses.COLOR_RED, -1)     # critical
        curses.init_pair(5, curses.COLOR_MAGENTA, -1) # graph accent
        self._colors_enabled = True

    def _color_by_percent(self, value: float):
        if not self._colors_enabled:
            return 0
        if value >= 90:
            return curses.color_pair(4) | curses.A_BOLD
        if value >= 75:
            return curses.color_pair(3) | curses.A_BOLD
        return curses.color_pair(2)

    def _stacked_dot_lines(self, values, width: int, levels: int):
        """Return stacked columns using '.' for points and ':' for vertical peak rise."""
        if width <= 0 or levels <= 0:
            return []

        data = self._sample_values(values, width)
        if not data:
            data = [0.0] * width

        # If we have fewer samples than visual columns, stretch them across
        # the full width so the chart looks compact and continuous.
        if len(data) < width:
            src = data
            data = []
            step = len(src) / float(width)
            i = 0.0
            while len(data) < width:
                data.append(float(src[min(len(src) - 1, int(i))]))
                i += step

        if self._unicode_graph:
            point_char = "█"
            rise_char = "▌"
        else:
            point_char = "."
            rise_char = ":"

        peak = max(max(data), 1.0)
        grid = [[" " for _ in range(len(data))] for _ in range(levels)]

        for x, val in enumerate(data):
            # Stable/base value is always shown as a point.
            grid[levels - 1][x] = point_char

            ratio = max(0.0, min(1.0, float(val) / peak))
            fill = int(round(ratio * levels))
            fill = max(1, min(levels, fill))

            # If value rises, use ':' as vertical connector and '.' at the top.
            if fill > 1:
                top_y = levels - fill
                for y in range(levels - 2, top_y, -1):
                    if 0 <= y < levels:
                        grid[y][x] = rise_char
                if 0 <= top_y < levels:
                    grid[top_y][x] = point_char
        return ["".join(row) for row in grid]

    @staticmethod
    def _trend_arrow(history) -> str:
        if len(history) < 2:
            return "-"
        prev = history[-2]
        curr = history[-1]
        if curr > prev + 0.5:
            return "^"
        if curr < prev - 0.5:
            return "v"
        return "-"

    @staticmethod
    def _sample_values(values, width: int):
        src = list(values)
        if width <= 0:
            return []
        if not src:
            return [0.0] * width
        if len(src) > width:
            step = len(src) / width
            sampled = []
            i = 0.0
            while len(sampled) < width:
                sampled.append(float(src[int(i)]))
                i += step
            return sampled
        if len(src) < width:
            return [float(v) for v in src]
        return [float(v) for v in src]

    def _draw_line_chart(
        self,
        stdscr,
        top: int,
        left: int,
        height: int,
        width: int,
        values,
        title: str,
        unit: str,
        max_value: float,
        style: int,
    ):
        if height < 4 or width < 20:
            return

        plot_width = width - 8
        data = self._sample_values(values, plot_width)
        if not data:
            return

        peak = max(max_value, max(data), 1.0)
        current = data[-1]
        avg = sum(data) / len(data)
        mn = min(data)
        mx = max(data)

        self._safe_addstr(
            stdscr,
            top - 1,
            left,
            f"{title} | now {current:.1f}{unit} avg {avg:.1f}{unit} min {mn:.1f}{unit} max {mx:.1f}{unit}",
            width,
            style,
        )

        y_values = []
        for val in data:
            ratio = max(0.0, min(1.0, val / peak))
            y = int(round((height - 1) * (1.0 - ratio)))
            y_values.append(max(0, min(height - 1, y)))

        for r in range(height):
            if r == 0:
                label = f"{peak:>5.0f}|"
            elif r == height - 1:
                label = f"{0:>5.0f}|"
            elif r == (height - 1) // 2:
                label = f"{peak/2:>5.0f}|"
            else:
                label = "     |"

            row_chars = [" "] * plot_width
            if r == (height - 1) // 2:
                for i in range(plot_width):
                    row_chars[i] = "-"

            for i, y in enumerate(y_values):
                if y == r:
                    row_chars[i] = "*"

            self._safe_addstr(stdscr, top + r, left, label + "".join(row_chars), width, style)

    def run(self):
        if curses is None:
            raise RuntimeError("curses module not available on this system")
        curses.wrapper(self._main)

    def _main(self, stdscr):
        self._init_colors()
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.keypad(True)

        while True:
            self._draw(stdscr)
            key = stdscr.getch()

            if key in (curses.KEY_UP, ord("k")):
                self.selected = (self.selected - 1) % len(self.menu_items)
            elif key in (curses.KEY_DOWN, ord("j")):
                self.selected = (self.selected + 1) % len(self.menu_items)
            elif key in (10, 13, curses.KEY_ENTER):
                if not self._execute_selected(stdscr):
                    break
            elif key in (ord("q"), 27):
                break

    def _draw(self, stdscr):
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        title = "Linux Hardware Diagnostic - TUI"
        title_style = (curses.color_pair(1) | curses.A_BOLD) if self._colors_enabled else curses.A_BOLD
        stdscr.addstr(1, max(0, (w - len(title)) // 2), title, title_style)
        stdscr.addstr(2, 2, "Use arrows (or j/k), Enter to select, q to quit")

        menu_top = 4
        for idx, item in enumerate(self.menu_items):
            style = curses.A_REVERSE if idx == self.selected else curses.A_NORMAL
            stdscr.addstr(menu_top + idx, 2, item[: max(0, w - 4)], style)

        details_top = menu_top + len(self.menu_items) + 2
        stdscr.addstr(details_top, 2, "Last message:", curses.A_BOLD)
        for i, line in enumerate(_wrap_text(self.last_message, w - 4)):
            if details_top + 1 + i >= h - 1:
                break
            stdscr.addstr(details_top + 1 + i, 2, line)

        result_top = details_top + 4
        if result_top < h - 1:
            stdscr.addstr(result_top, 2, "Results:", curses.A_BOLD)

        row = result_top + 1
        for res in self.results[-5:]:
            text = f"[{res['status'].upper()}] {res['component']}: {res['message']}"
            for line in _wrap_text(text, w - 4):
                if row >= h - 1:
                    break
                stdscr.addstr(row, 2, line)
                row += 1
            if row >= h - 1:
                break

        stdscr.refresh()

    def _execute_selected(self, stdscr) -> bool:
        action = self.menu_items[self.selected]

        try:
            if action == "Run CPU Test":
                self._append_result(_run_cpu())
            elif action == "Run Disks Test":
                self._append_result(_run_disks())
            elif action == "Run GPU Test":
                self._append_result(_run_gpu())
            elif action == "Run Network Test":
                self._append_result(_run_network())
            elif action == "Run USB Test":
                self._append_result(_run_usb())
            elif action == "Realtime Monitor":
                self._run_monitor_view(stdscr)
                self.last_message = "Exited realtime monitor"
            elif action == "Run All Tests":
                self._append_result(_run_cpu())
                self._append_result(_run_disks())
                self._append_result(_run_gpu())
                self._append_result(_run_network())
                self._append_result(_run_usb())
                self.last_message = "All tests executed"
            elif action == "Save Report":
                self._save_report()
            elif action == "Clear Results":
                self.results.clear()
                self.last_message = "Results cleared"
            elif action == "Quit":
                return False
        except Exception as exc:
            self.last_message = f"Error: {exc}"

        return True

    def _append_result(self, result: Dict[str, Any]):
        self.results.append(result)
        self.last_message = f"{result['component']} -> {result['status']}"

    def _save_report(self):
        report = report_gen.Report()
        report.add_result(cpu_test.cpu_test())
        report.add_result(disks_test.disks_test())
        report.add_result(gpu_test.gpu_test())
        report.add_result(network_test.network_test())
        report.add_result(usb_test.usb_test())
        path = report.save_report("auto")
        self.last_message = f"Report saved: {path}"

    @staticmethod
    def _safe_addstr(stdscr, row: int, col: int, text: str, width: int, style=0):
        if row < 0 or col < 0 or width <= 0:
            return
        try:
            stdscr.addstr(row, col, text[:width], style)
        except curses.error:
            pass

    def _draw_metric_card(
        self,
        stdscr,
        top: int,
        left: int,
        width: int,
        height: int,
        title: str,
        current_text: str,
        history,
        color_value: float,
        highlighted: bool,
    ):
        if width < 18 or height < 7:
            return

        border_style = curses.A_BOLD if highlighted else 0
        if self._colors_enabled:
            border_style |= curses.color_pair(1 if highlighted else 5)

        graph_style = self._color_by_percent(color_value)
        if highlighted:
            graph_style |= curses.A_BOLD

        top_border = "+" + "-" * (width - 2) + "+"
        mid_border = "|" + " " * (width - 2) + "|"
        self._safe_addstr(stdscr, top, left, top_border, width, border_style)
        for r in range(1, height - 1):
            self._safe_addstr(stdscr, top + r, left, mid_border, width, border_style)
        self._safe_addstr(stdscr, top + height - 1, left, top_border, width, border_style)

        trend = self._trend_arrow(history)
        self._safe_addstr(stdscr, top + 1, left + 2, f"{title} {trend}", width - 4, border_style)
        self._safe_addstr(stdscr, top + 2, left + 2, current_text, width - 4, graph_style)

        spark_width = max(6, width - 4)
        chart_start = top + 3
        inner_bottom = top + height - 2

        # Give more vertical space to the chart so ':' stacks are visible.
        show_stats = height >= 9
        stats_row = inner_bottom if show_stats else None
        chart_end = (stats_row - 1) if show_stats else inner_bottom
        chart_rows = max(2, chart_end - chart_start + 1)

        dot_lines = self._stacked_dot_lines(history, width=spark_width, levels=chart_rows)
        chart_style = curses.color_pair(5) if self._colors_enabled else 0

        for i, line in enumerate(dot_lines[:chart_rows]):
            self._safe_addstr(stdscr, chart_start + i, left + 2, line, width - 4, chart_style)

        if history and show_stats and stats_row is not None and stats_row >= chart_start:
            mn = min(history)
            mx = max(history)
            self._safe_addstr(stdscr, stats_row, left + 2, f"min {mn:.1f}  max {mx:.1f}", width - 4)

    def _run_monitor_view(self, stdscr):
        self._init_colors()
        stdscr.nodelay(True)
        stdscr.keypad(True)

        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            if w >= 86:
                cols = 3
            elif w >= 58:
                cols = 2
            else:
                cols = 1

            card_gap = 1
            card_w = max(18, (w - 4 - (cols - 1) * card_gap) // cols)
            cards_top = 5

            metric_count = 5
            rows = (metric_count + cols - 1) // cols

            # Keep enough chart rows to create a btop-like stacked effect with ':'.
            # If terminal is small, process table shrinks but charts remain expressive.
            min_proc_block = 4  # title + header + minimal process rows
            available_for_cards = max(0, h - cards_top - min_proc_block)
            card_h = max(7, min(11, available_for_cards // max(1, rows)))
            cards_height = rows * card_h

            proc_top = cards_top + cards_height + 1
            top_n = max(3, h - (proc_top + 3))
            snap = self.monitor.snapshot(top_n=top_n)

            self.cpu_history.append(float(snap["cpu_percent"]))
            self.mem_history.append(float(snap["memory"]["percent"]))
            net_rate = float(snap["network"]["download_bps"] + snap["network"]["upload_bps"])
            self.net_history.append(net_rate)
            self.swap_history.append(float(snap["swap"]["percent"]))
            disk_percent = snap["disk"]["percent"] if snap["disk"]["percent"] is not None else 0.0
            self.disk_history.append(float(disk_percent))

            title_style = (curses.color_pair(1) | curses.A_BOLD) if self._colors_enabled else curses.A_BOLD

            self._safe_addstr(stdscr, 1, 2, "Realtime Resource Monitor (Task-Manager style)", w - 4, title_style)
            self._safe_addstr(
                stdscr,
                2,
                2,
                "q/Esc exit | c/m/n/s/d or 1..5 focus card | Tab cycle | u toggle Unicode/ASCII",
                w - 4,
            )

            if self._unicode_graph:
                legend_text = "Legend: ^ up, v down, - stable | chart: █ points and ▌ stacked vertically for peaks"
            else:
                legend_text = "Legend: ^ up, v down, - stable | chart: '.' points and ':' stacked vertically for peaks"
            self._safe_addstr(
                stdscr,
                3,
                2,
                legend_text,
                w - 4,
            )

            net = snap["network"]
            net_load = 0.0 if not self.net_history else min(100.0, (self.net_history[-1] / (100 * 1024 * 1024)) * 100.0)
            disk = snap["disk"]

            metrics = [
                {
                    "key": "cpu",
                    "title": "CPU",
                    "text": f"{snap['cpu_percent']:.1f}%",
                    "history": self.cpu_history,
                    "color": float(snap["cpu_percent"]),
                },
                {
                    "key": "mem",
                    "title": "RAM",
                    "text": f"{snap['memory']['percent']:.1f}%",
                    "history": self.mem_history,
                    "color": float(snap["memory"]["percent"]),
                },
                {
                    "key": "net",
                    "title": "NET",
                    "text": f"d {human_bytes(net['download_bps'])}/s u {human_bytes(net['upload_bps'])}/s",
                    "history": self.net_history,
                    "color": net_load,
                },
                {
                    "key": "swap",
                    "title": "SWAP",
                    "text": f"{snap['swap']['percent']:.1f}%",
                    "history": self.swap_history,
                    "color": float(snap["swap"]["percent"]),
                },
                {
                    "key": "disk",
                    "title": "DISK",
                    "text": "n/a" if disk["percent"] is None else f"{disk['percent']:.1f}%",
                    "history": self.disk_history,
                    "color": float(disk_percent),
                },
            ]

            for i, metric in enumerate(metrics):
                row = i // cols
                col = i % cols
                left = 2 + col * (card_w + card_gap)
                top = cards_top + row * card_h
                self._draw_metric_card(
                    stdscr,
                    top=top,
                    left=left,
                    width=card_w,
                    height=card_h,
                    title=metric["title"],
                    current_text=metric["text"],
                    history=metric["history"],
                    color_value=metric["color"],
                    highlighted=(self.monitor_focus == metric["key"]),
                )

            self._safe_addstr(stdscr, proc_top - 2, 2, "Focused card = brighter border and text", w - 4)
            self._safe_addstr(stdscr, proc_top - 1, 2, f"Uptime: {snap['uptime']}", w - 4)
            self._safe_addstr(stdscr, proc_top, 2, "Top processes by CPU", w - 4, title_style)
            self._safe_addstr(stdscr, proc_top + 1, 2, "PID      CPU%    MEM%    NAME", w - 4)

            row = proc_top + 2
            for proc in snap["processes"]:
                line = f"{proc['pid']:<8} {proc['cpu_percent']:>5.1f}   {proc['memory_percent']:>5.1f}   {proc['name']}"
                self._safe_addstr(stdscr, row, 2, line, w - 4, self._color_by_percent(float(proc["cpu_percent"])))
                row += 1
                if row >= h - 1:
                    break

            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord("q"), 27):
                break
            elif key in (ord("c"), ord("1")):
                self.monitor_focus = "cpu"
            elif key in (ord("m"), ord("2")):
                self.monitor_focus = "mem"
            elif key in (ord("n"), ord("3")):
                self.monitor_focus = "net"
            elif key in (ord("s"), ord("4")):
                self.monitor_focus = "swap"
            elif key in (ord("d"), ord("5")):
                self.monitor_focus = "disk"
            elif key == 9:  # Tab
                order = ["cpu", "mem", "net", "swap", "disk"]
                idx = order.index(self.monitor_focus)
                self.monitor_focus = order[(idx + 1) % len(order)]
            elif key in (ord("u"), ord("U")):
                self._unicode_graph = not self._unicode_graph
            time.sleep(1.0)

        stdscr.nodelay(False)

    def run_monitor_only(self):
        if curses is None:
            raise RuntimeError("curses module not available on this system")
        curses.wrapper(self._run_monitor_view)


def launch_tui():
    try:
        if curses is None:
            print("Unable to start TUI: curses is not available on this system.")
            return
        app = DiagnosticTUI()
        app.run()
    except curses.error:
        print("Unable to start TUI: terminal does not support curses.")
    except Exception:
        print("Unexpected TUI error:")
        print(traceback.format_exc())


def launch_realtime_monitor():
    try:
        if curses is None:
            print("Unable to start monitor: curses is not available on this system.")
            return
        app = DiagnosticTUI()
        app.run_monitor_only()
    except curses.error:
        print("Unable to start monitor: terminal does not support curses.")
    except Exception:
        print("Unexpected monitor error:")
        print(traceback.format_exc())


if __name__ == "__main__":
    launch_tui()
