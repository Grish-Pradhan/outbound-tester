import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import time
from datetime import datetime

class OutboundTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Outbound Connection Tester")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e293b")
        
        self.is_running = False
        self.stop_flag = False
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#1e293b')
        style.configure('TLabel', background='#1e293b', foreground='#e2e8f0', font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#ffffff')
        style.configure('TButton', font=('Arial', 10, 'bold'))
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header Frame
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=20, pady=20)
        
        title = ttk.Label(header_frame, text="Outbound Connection Tester", style='Title.TLabel')
        title.pack(anchor='w')
        
        subtitle = ttk.Label(header_frame, text="Test outbound connections for network security analysis", 
                           font=('Arial', 9), foreground='#94a3b8')
        subtitle.pack(anchor='w', pady=(5, 0))
        
        # Warning Frame
        warning_frame = tk.Frame(self.root, bg='#78350f', bd=1, relief='solid')
        warning_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        warning_text = "⚠️ Important: Only test networks you own or have explicit permission to test."
        warning_label = tk.Label(warning_frame, text=warning_text, bg='#78350f', 
                                fg='#fef3c7', font=('Arial', 9, 'bold'), pady=10)
        warning_label.pack()
        
        # Configuration Frame
        config_frame = tk.LabelFrame(self.root, text=" Configuration ", bg='#334155', 
                                    fg='#e2e8f0', font=('Arial', 11, 'bold'), padx=15, pady=15)
        config_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Target Host
        tk.Label(config_frame, text="Target Host:", bg='#334155', fg='#e2e8f0', 
                font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.host_entry = tk.Entry(config_frame, width=40, font=('Arial', 10))
        self.host_entry.insert(0, "example.com")
        self.host_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Ports
        tk.Label(config_frame, text="Ports (comma-separated):", bg='#334155', fg='#e2e8f0',
                font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.ports_entry = tk.Entry(config_frame, width=40, font=('Arial', 10))
        self.ports_entry.insert(0, "80,443,8080,3389,22,21,25,53")
        self.ports_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Timeout
        tk.Label(config_frame, text="Timeout (seconds):", bg='#334155', fg='#e2e8f0',
                font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.timeout_entry = tk.Entry(config_frame, width=40, font=('Arial', 10))
        self.timeout_entry.insert(0, "3")
        self.timeout_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        config_frame.columnconfigure(1, weight=1)
        
        # Buttons Frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.start_btn = tk.Button(button_frame, text="▶ Start Test", command=self.start_test,
                                   bg='#2563eb', fg='white', font=('Arial', 10, 'bold'),
                                   padx=20, pady=8, cursor='hand2')
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = tk.Button(button_frame, text="■ Stop", command=self.stop_test,
                                  bg='#dc2626', fg='white', font=('Arial', 10, 'bold'),
                                  padx=20, pady=8, cursor='hand2', state='disabled')
        self.stop_btn.pack(side='left')
        
        self.clear_btn = tk.Button(button_frame, text="Clear Results", command=self.clear_results,
                                   bg='#64748b', fg='white', font=('Arial', 10, 'bold'),
                                   padx=20, pady=8, cursor='hand2')
        self.clear_btn.pack(side='left', padx=(10, 0))
        
        # Progress Frame
        self.progress_frame = ttk.Frame(self.root)
        self.progress_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        self.progress_label = ttk.Label(self.progress_frame, text="Ready to test", foreground='#94a3b8')
        self.progress_label.pack(anchor='w')
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=300)
        self.progress_bar.pack(fill='x', pady=(5, 0))
        
        # Results Frame
        results_frame = tk.LabelFrame(self.root, text=" Test Results ", bg='#334155',
                                     fg='#e2e8f0', font=('Arial', 11, 'bold'), padx=15, pady=15)
        results_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Results Text Widget with Scrollbar
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, 
                                                      font=('Courier', 9), bg='#0f172a',
                                                      fg='#e2e8f0', height=15)
        self.results_text.pack(fill='both', expand=True)
        
        # Configure text tags for colored output
        self.results_text.tag_config('header', foreground='#60a5fa', font=('Courier', 9, 'bold'))
        self.results_text.tag_config('open', foreground='#22c55e')
        self.results_text.tag_config('closed', foreground='#ef4444')
        self.results_text.tag_config('filtered', foreground='#eab308')
        self.results_text.tag_config('error', foreground='#f97316')
        self.results_text.tag_config('info', foreground='#94a3b8')
        self.results_text.tag_config('summary', foreground='#a78bfa', font=('Courier', 9, 'bold'))
        
    def log_result(self, message, tag='info'):
        self.results_text.insert(tk.END, message + '\n', tag)
        self.results_text.see(tk.END)
        self.results_text.update()
        
    def test_port(self, host, port, timeout):
        """Test a single port"""
        start_time = time.time()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            sock.close()
            
            if result == 0:
                return 'open', elapsed, 'Connection successful'
            else:
                return 'closed', elapsed, 'Connection refused'
                
        except socket.timeout:
            elapsed = (time.time() - start_time) * 1000
            return 'filtered', elapsed, 'Connection timeout'
        except socket.gaierror:
            return 'error', 0, 'Hostname resolution failed'
        except Exception as e:
            return 'error', 0, str(e)
            
    def run_test(self):
        """Main test execution thread"""
        host = self.host_entry.get().strip()
        ports_str = self.ports_entry.get().strip()
        timeout_str = self.timeout_entry.get().strip()
        
        # Validation
        if not host:
            messagebox.showerror("Error", "Please enter a target host")
            self.reset_ui()
            return
            
        try:
            timeout = float(timeout_str)
            if timeout <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid timeout value")
            self.reset_ui()
            return
            
        try:
            ports = [int(p.strip()) for p in ports_str.split(',') if p.strip()]
            if not ports:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid ports format")
            self.reset_ui()
            return
            
        # Start testing
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_result(f"{'='*70}", 'header')
        self.log_result(f"Test started at {timestamp}", 'header')
        self.log_result(f"Target: {host} | Ports: {len(ports)} | Timeout: {timeout}s", 'header')
        self.log_result(f"{'='*70}\n", 'header')
        
        results = {'open': 0, 'closed': 0, 'filtered': 0, 'error': 0}
        
        self.progress_bar['maximum'] = len(ports)
        
        for i, port in enumerate(ports):
            if self.stop_flag:
                self.log_result("\n[TEST STOPPED BY USER]\n", 'error')
                break
                
            self.progress_label.config(text=f"Testing port {port}... ({i+1}/{len(ports)})")
            self.progress_bar['value'] = i + 1
            
            status, elapsed, message = self.test_port(host, port, timeout)
            results[status] += 1
            
            # Format output
            status_symbol = {
                'open': '✓',
                'closed': '✗',
                'filtered': '◐',
                'error': '!'
            }.get(status, '?')
            
            output = f"{status_symbol} Port {port:5d} | {status.upper():8s} | {elapsed:6.0f}ms | {message}"
            self.log_result(output, status)
            
        # Summary
        if not self.stop_flag:
            self.log_result(f"\n{'='*70}", 'summary')
            self.log_result("TEST SUMMARY", 'summary')
            self.log_result(f"{'='*70}", 'summary')
            self.log_result(f"Total Ports Tested: {sum(results.values())}", 'summary')
            self.log_result(f"Open:     {results['open']}", 'open')
            self.log_result(f"Closed:   {results['closed']}", 'closed')
            self.log_result(f"Filtered: {results['filtered']}", 'filtered')
            self.log_result(f"Errors:   {results['error']}", 'error')
            self.log_result(f"{'='*70}\n", 'summary')
            
        self.reset_ui()
        
    def start_test(self):
        """Start the test in a separate thread"""
        if self.is_running:
            return
            
        self.is_running = True
        self.stop_flag = False
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.clear_btn.config(state='disabled')
        
        # Run test in separate thread to keep GUI responsive
        test_thread = threading.Thread(target=self.run_test, daemon=True)
        test_thread.start()
        
    def stop_test(self):
        """Stop the running test"""
        self.stop_flag = True
        self.stop_btn.config(state='disabled')
        
    def reset_ui(self):
        """Reset UI after test completion"""
        self.is_running = False
        self.stop_flag = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.clear_btn.config(state='normal')
        self.progress_label.config(text="Test completed")
        
    def clear_results(self):
        """Clear the results text area"""
        self.results_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Ready to test")

def main():
    root = tk.Tk()
    app = OutboundTester(root)
    root.mainloop()

if __name__ == "__main__":
    main()
