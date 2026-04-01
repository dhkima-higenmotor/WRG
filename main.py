import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as patches
import numpy as np
import ezdxf

class WaveGearApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wave Roller Gear Generator")
        # 제어 패널만 남으므로 창 크기를 작게 조절
        self.root.geometry("350x800")

        # 독립된 플롯 창을 관리하기 위한 변수
        self.plot_window = None
        self.fig = None
        self.ax = None
        self.canvas = None

        # 제어할 파라미터 변수 초기화 (기본값 설정)
        self.roller_diameter_var = tk.DoubleVar(value=3.0)
        self.ecc_var = tk.DoubleVar(value=0.6)
        self.rollers_num_var = tk.IntVar(value=8)
        self.wave_gen_d_var = tk.DoubleVar(value=9.6)
        self.input_shaft_diameter_var = tk.DoubleVar(value=5.0)
        self.resolution_var = tk.IntVar(value=500)

        self.setup_ui()
        self.update_plot()  # 초기 그래프 그리기

    def setup_ui(self):
        # 컨트롤 패널 UI 구성
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(control_frame, text="[WRG] Wave Roller Gearbox", font=("Helvetica", 14, "bold")).pack(pady=(0, 20))

        self.create_input_field(control_frame, "Roller Diameter (mm):", self.roller_diameter_var)
        self.create_input_field(control_frame, "Eccentricity (ecc) (mm):", self.ecc_var)
        self.create_input_field(control_frame, "Rollers Number:", self.rollers_num_var)
        self.create_input_field(control_frame, "Wave Generator Diameter (mm):", self.wave_gen_d_var)
        self.create_input_field(control_frame, "Input Shaft Diameter (mm):", self.input_shaft_diameter_var)
        self.create_input_field(control_frame, "Resolution (res):", self.resolution_var)

        # Update Graphics 버튼
        update_btn = ttk.Button(control_frame, text="Update Graphics", command=self.update_plot)
        update_btn.pack(pady=(20, 5), fill=tk.X)

        # Export DXF 버튼
        export_btn = ttk.Button(control_frame, text="Export DXF", command=self.export_dxf)
        export_btn.pack(pady=5, fill=tk.X)

        # 결과 텍스트 표시
        self.output_text = tk.Text(control_frame, height=12, font=("Helvetica", 10), state=tk.NORMAL)
        self.output_text.insert(tk.END, "Waiting for graphics update...")
        self.output_text.config(state=tk.DISABLED)
        self.output_text.pack(pady=10, fill=tk.BOTH, expand=True)

    def create_input_field(self, parent, label_text, variable):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text=label_text).pack(anchor=tk.W)
        ttk.Entry(frame, textvariable=variable).pack(fill=tk.X)

    def cycloid_points(self, ecc, roll_r, wave_gen_r, rollers_num, cav_num, res=None):
        if res is None:
            res = self.resolution_var.get()
        points = []
        for i in range(res):
            theta = (i / res) * 2 * np.pi

            val_inside_sqrt = (roll_r + wave_gen_r) ** 2 - (ecc * np.sin(cav_num * theta)) ** 2
            if val_inside_sqrt < 0: val_inside_sqrt = 0
            
            s_rol = np.sqrt(val_inside_sqrt)
            l_rol = ecc * np.cos(cav_num * theta) + s_rol
            xi = np.arctan2(ecc * cav_num * np.sin(cav_num * theta), s_rol)

            x = l_rol * np.sin(theta) + roll_r * np.sin(theta + xi)
            y = l_rol * np.cos(theta) + roll_r * np.cos(theta + xi)

            points.append((x, y))
        points.append(points[0])
        return np.array(points)

    def draw_circle(self, center, radius, **kwargs):
        # pyplot 대신 matplotlib.patches 사용
        circle = patches.Circle(center, radius, **kwargs)
        self.ax.add_patch(circle)

    def plot_rols(self, cy_r, wave_gen_r, roll_r, ecc, rollers_num, cav_num):
        theta = np.linspace(0, 2 * np.pi, rollers_num, endpoint=False)
        for t in theta:
            val_inside_sqrt = (roll_r + wave_gen_r) ** 2 - (ecc * np.sin(cav_num * t)) ** 2
            if val_inside_sqrt < 0: val_inside_sqrt = 0
                
            s_rol = np.sqrt(val_inside_sqrt)
            l_rol = ecc * np.cos(cav_num * t) + s_rol
            x = l_rol * np.sin(t)
            y = l_rol * np.cos(t)
            self.draw_circle((x, y), roll_r, fill=True, color='orange', alpha=0.7)

    def update_plot(self):
        try:
            roller_diameter = self.roller_diameter_var.get()
            ecc = self.ecc_var.get()
            rollers_num = self.rollers_num_var.get()
            wave_gen_r_input = self.wave_gen_d_var.get() / 2.0
            input_shaft_diameter = self.input_shaft_diameter_var.get()
            resolution = self.resolution_var.get()
        except tk.TclError:
            messagebox.showerror("Error", "The input value is incorrect.")
            return

        # 1. 독립된 Toplevel 창이 없거나 닫혔으면 새로 생성
        if self.plot_window is None or not self.plot_window.winfo_exists():
            self.plot_window = tk.Toplevel(self.root)
            self.plot_window.title("Wave Roller Gear - Plot Window")
            self.plot_window.geometry("700x750")

            # Figure 객체 생성
            self.fig = Figure(figsize=(8, 8))
            self.ax = self.fig.add_subplot(111)

            # 캔버스 생성 및 배치
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_window)
            
            # 확대/축소/저장 등을 위한 표준 툴바(NavigationToolbar) 추가
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_window)
            self.toolbar.update()
            
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # 창을 닫을 때 메모리 해제를 위한 이벤트 바인딩
            self.plot_window.protocol("WM_DELETE_WINDOW", self.on_close_plot)
        else:
            # 창이 이미 있으면 앞으로 가져오고 그래프 초기화
            self.plot_window.lift()
            self.ax.clear()

        # 2. 기어 계산 로직
        cav_num = rollers_num + 1
        cy_r_min = (1.1 * roller_diameter) / np.sin(np.pi / cav_num) + 2 * ecc
        wave_gen_r_min = float((cy_r_min - 2 * ecc) - roller_diameter)
        wave_gen_r = float(max(wave_gen_r_input, wave_gen_r_min))
        cy_r = float(wave_gen_r + 2 * ecc + roller_diameter)
        roll_r = float(roller_diameter / 2)

        # 3. 그래프 그리기
        self.ax.set_aspect('equal')
        limit = cy_r + (roller_diameter * 2)
        self.ax.set_xlim(-limit, limit)
        self.ax.set_ylim(-limit, limit)
        self.ax.set_title("[WRG] Wave Roller Gearbox")
        
        # 그리드 추가 (점선, 반투명)
        self.ax.grid(True, linestyle='--', alpha=0.6)

        cycloid = self.cycloid_points(ecc, roll_r, wave_gen_r, rollers_num, cav_num, res=resolution)
        self.ax.plot(cycloid[:, 0], cycloid[:, 1], label='Cycloidal Ring Gear', color='blue')

        sep_width = 2.2 * ecc
        sep_middle_radius = wave_gen_r + roll_r
        sep_outer_radius = sep_middle_radius + sep_width / 2
        sep_inner_radius = sep_middle_radius - sep_width / 2

        info_str = (
            f"--- Input Parameters ---\n"
            f"Roller Diameter: {roller_diameter:.2f} mm\n"
            f"Eccentricity: {ecc:.2f} mm\n"
            f"Rollers Number: {rollers_num}\n"
            f"Wave Gen Diameter: {wave_gen_r_input*2:.2f} mm\n"
            f"Input Shaft Diameter: {input_shaft_diameter:.2f} mm\n"
            f"Resolution: {resolution}\n\n"
            f"--- Calculated Dimensions ---\n"
            f"Ring Gear Outer Diameter: {cy_r * 2:.2f} mm\n"
            f"Separator Inner Diameter: {sep_inner_radius * 2:.2f} mm\n"
            f"Separator Outer Diameter: {sep_outer_radius * 2:.2f} mm\n\n"
            f"--- Kinematics ---\n"
            f"Reduction Ratio (Ring fixed): 1/{rollers_num} (Reverse)\n"
            f"Reduction Ratio (Separator fixed): 1/{cav_num} (Forward)"
        )
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, info_str)
        self.output_text.config(state=tk.DISABLED)

        self.draw_circle((0, 0), sep_outer_radius, fill=False, linestyle='--', color='green', label='Separator')
        self.draw_circle((0, 0), sep_inner_radius, fill=False, linestyle='--', color='green')

        self.plot_rols(cy_r, wave_gen_r, roll_r, ecc, rollers_num, cav_num)
        self.draw_circle((0, ecc), wave_gen_r, fill=False, linestyle='-.', color='red', label='Wave Generator')
        self.draw_circle((0, 0), input_shaft_diameter / 2, fill=False, color='purple', linestyle=':', label='Input Shaft')

        self.ax.legend(loc='upper right')

        # 플롯 여백 최소화
        self.fig.tight_layout()

        # 캔버스 렌더링 업데이트
        self.canvas.draw()

    def on_close_plot(self):
        # 플롯 창이 닫힐 때 자원 정리
        self.plot_window.destroy()
        self.plot_window = None
        self.fig = None
        self.ax = None
        self.canvas = None

    def export_dxf(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".dxf",
            filetypes=[("DXF Files", "*.dxf"), ("All Files", "*.*")],
            title="Save DXF File"
        )
        
        if not filepath:
            return 

        try:
            roller_diameter = self.roller_diameter_var.get()
            ecc = self.ecc_var.get()
            rollers_num = self.rollers_num_var.get()
            wave_gen_r_input = self.wave_gen_d_var.get() / 2.0
            input_shaft_diameter = self.input_shaft_diameter_var.get()
            resolution = self.resolution_var.get()
        except tk.TclError:
            messagebox.showerror("Error", "The input value is incorrect.")
            return

        cav_num = rollers_num + 1
        cy_r_min = (1.1 * roller_diameter) / np.sin(np.pi / cav_num) + 2 * ecc
        wave_gen_r_min = float((cy_r_min - 2 * ecc) - roller_diameter)
        wave_gen_r = float(max(wave_gen_r_input, wave_gen_r_min))
        cy_r = float(wave_gen_r + 2 * ecc + roller_diameter)
        roll_r = float(roller_diameter / 2)

        try:
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()

            cycloid = self.cycloid_points(ecc, roll_r, wave_gen_r, rollers_num, cav_num, res=resolution)
            msp.add_lwpolyline(cycloid.tolist(), close=True)

            sep_width = 2.2 * ecc
            sep_middle_radius = wave_gen_r + roll_r
            sep_outer_radius = sep_middle_radius + sep_width / 2
            sep_inner_radius = sep_middle_radius - sep_width / 2
            msp.add_circle((0, 0), sep_outer_radius)
            msp.add_circle((0, 0), sep_inner_radius)

            theta = np.linspace(0, 2 * np.pi, rollers_num, endpoint=False)
            for t in theta:
                val_inside_sqrt = (roll_r + wave_gen_r) ** 2 - (ecc * np.sin(cav_num * t)) ** 2
                if val_inside_sqrt < 0: val_inside_sqrt = 0
                    
                s_rol = np.sqrt(val_inside_sqrt)
                l_rol = ecc * np.cos(cav_num * t) + s_rol
                x = l_rol * np.sin(t)
                y = l_rol * np.cos(t)
                msp.add_circle((x, y), roll_r)

            msp.add_circle((0, ecc), wave_gen_r)
            msp.add_circle((0, 0), input_shaft_diameter / 2)

            doc.saveas(filepath)
            messagebox.showinfo("Success", f"Successfully exported to:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred while saving the DXF file:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WaveGearApp(root)
    root.mainloop()