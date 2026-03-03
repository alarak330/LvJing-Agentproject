"""
法律智能体类案报告生成系统 - 主程序

提供GUI界面，支持上传Word/PDF文件并输入问题，生成Markdown格式的法律类案报告。
"""

from __future__ import annotations

import os
import sys
import json
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import dotenv

# 加载环境变量
dotenv.load_dotenv()

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入智能体模块
from forum import ForumAgent

# 动态导入 ReportAgent（因为目录名包含空格）
import importlib.util

def _import_report_agent():
    """动态导入 ReportAgent"""
    project_root = Path(__file__).parent
    report_agent_dir = project_root / "report agent"
    report_agent_path = report_agent_dir / "agent.py"
    
    # 添加目录到路径
    parent_str = str(report_agent_dir)
    if parent_str not in sys.path:
        sys.path.insert(0, parent_str)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 创建包名（替换空格为下划线）
    package_name = "report_agent"
    
    # 先创建并注册包模块，以便相对导入可以工作
    if package_name not in sys.modules:
        package_module = type(sys)(package_name)
        package_module.__path__ = [str(report_agent_dir)]
        package_module.__file__ = str(report_agent_dir / "__init__.py") if (report_agent_dir / "__init__.py").exists() else None
        package_module.__package__ = package_name
        sys.modules[package_name] = package_module
    
    # 预加载子模块及其依赖
    # 先创建 llm 包模块
    llm_dir = report_agent_dir / "llm"
    if llm_dir.exists():
        llm_package_name = f"{package_name}.llm"
        if llm_package_name not in sys.modules:
            llm_package_module = type(sys)(llm_package_name)
            llm_package_module.__path__ = [str(llm_dir)]
            llm_package_module.__file__ = str(llm_dir / "__init__.py") if (llm_dir / "__init__.py").exists() else None
            llm_package_module.__package__ = llm_package_name
            sys.modules[llm_package_name] = llm_package_module
        
        # 先加载 llm 子模块中的 kimimodels.py
        kimimodels_path = llm_dir / "kimimodels.py"
        if kimimodels_path.exists():
            kimimodels_name = f"{llm_package_name}.kimimodels"
            if kimimodels_name not in sys.modules:
                try:
                    kimimodels_spec = importlib.util.spec_from_file_location(
                        kimimodels_name,
                        kimimodels_path,
                        submodule_search_locations=[str(llm_dir)]
                    )
                    if kimimodels_spec and kimimodels_spec.loader:
                        kimimodels_module = importlib.util.module_from_spec(kimimodels_spec)
                        kimimodels_module.__package__ = llm_package_name
                        kimimodels_module.__name__ = kimimodels_name
                        sys.modules[kimimodels_name] = kimimodels_module
                        kimimodels_spec.loader.exec_module(kimimodels_module)
                except Exception as e:
                    print(f"警告: 加载 kimimodels 时出错: {e}")
        
        # 然后加载 llm/__init__.py
        llm_init_path = llm_dir / "__init__.py"
        if llm_init_path.exists():
            # 检查是否已经加载了实际的 __init__.py 内容
            llm_module = sys.modules.get(llm_package_name)
            if llm_module is None or not hasattr(llm_module, 'get_chat_model'):
                try:
                    llm_spec = importlib.util.spec_from_file_location(
                        llm_package_name,
                        llm_init_path,
                        submodule_search_locations=[str(llm_dir)]
                    )
                    if llm_spec and llm_spec.loader:
                        llm_module = importlib.util.module_from_spec(llm_spec)
                        llm_module.__package__ = llm_package_name  # 应该是 report_agent.llm
                        llm_module.__name__ = llm_package_name
                        sys.modules[llm_package_name] = llm_module
                        llm_spec.loader.exec_module(llm_module)
                except Exception as e:
                    print(f"警告: 加载 llm 模块时出错: {e}")
                    import traceback
                    traceback.print_exc()
    
    # 加载 prompt 子模块
    prompt_dir = report_agent_dir / "prompt"
    if prompt_dir.exists():
        # 先创建 prompt 包模块
        prompt_package_name = f"{package_name}.prompt"
        if prompt_package_name not in sys.modules:
            prompt_package_module = type(sys)(prompt_package_name)
            prompt_package_module.__path__ = [str(prompt_dir)]
            prompt_package_module.__file__ = str(prompt_dir / "__init__.py") if (prompt_dir / "__init__.py").exists() else None
            prompt_package_module.__package__ = prompt_package_name
            sys.modules[prompt_package_name] = prompt_package_module
        
        # 先加载 prompt 子模块中的依赖文件
        for dep_file in ["base.py", "report_prompts.py"]:
            dep_path = prompt_dir / dep_file
            if dep_path.exists():
                dep_name = f"{prompt_package_name}.{dep_path.stem}"
                if dep_name not in sys.modules:
                    try:
                        dep_spec = importlib.util.spec_from_file_location(
                            dep_name,
                            dep_path,
                            submodule_search_locations=[str(prompt_dir)]
                        )
                        if dep_spec and dep_spec.loader:
                            dep_module = importlib.util.module_from_spec(dep_spec)
                            dep_module.__package__ = prompt_package_name
                            dep_module.__name__ = dep_name
                            sys.modules[dep_name] = dep_module
                            dep_spec.loader.exec_module(dep_module)
                    except Exception as e:
                        print(f"警告: 加载 {dep_file} 时出错: {e}")
        
        # 然后加载 prompt/__init__.py
        if (prompt_dir / "__init__.py").exists():
            # 检查是否已经加载了实际的 __init__.py 内容
            prompt_module = sys.modules.get(prompt_package_name)
            if prompt_module is None or not hasattr(prompt_module, 'REPORT_GENERATION_PROMPT'):
                try:
                    prompt_spec = importlib.util.spec_from_file_location(
                        prompt_package_name,
                        prompt_dir / "__init__.py",
                        submodule_search_locations=[str(prompt_dir)]
                    )
                    if prompt_spec and prompt_spec.loader:
                        prompt_module = importlib.util.module_from_spec(prompt_spec)
                        prompt_module.__package__ = prompt_package_name  # 应该是 report_agent.prompt
                        prompt_module.__name__ = prompt_package_name
                        sys.modules[prompt_package_name] = prompt_module
                        prompt_spec.loader.exec_module(prompt_module)
                except Exception as e:
                    print(f"警告: 加载 prompt 模块时出错: {e}")
                    import traceback
                    traceback.print_exc()
    
    # 加载主模块
    spec = importlib.util.spec_from_file_location(
        f"{package_name}.agent",
        report_agent_path,
        submodule_search_locations=[str(report_agent_dir)]
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块 agent from {report_agent_path}")
    
    module = importlib.util.module_from_spec(spec)
    module.__package__ = package_name
    module.__name__ = f"{package_name}.agent"
    sys.modules[f"{package_name}.agent"] = module
    spec.loader.exec_module(module)
    
    return module.ReportAgent

ReportAgent = _import_report_agent()

# 导入日志
from loguru import logger

# 配置日志
# 创建log文件夹
log_dir = Path(__file__).parent / "log"
log_dir.mkdir(exist_ok=True)

# 移除默认日志处理器
logger.remove()

# 添加控制台输出（INFO级别）
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

# 添加文件输出（所有级别，按日期轮转）
logger.add(
    log_dir / "app_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="DEBUG",
    rotation="00:00",  # 每天午夜轮转
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    encoding="utf-8"
)

# 添加错误日志单独文件
logger.add(
    log_dir / "error_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="ERROR",
    rotation="00:00",
    retention="90 days",  # 错误日志保留更久
    compression="zip",
    encoding="utf-8"
)

logger.info(f"日志已配置，日志文件保存在: {log_dir}")


class LegalReportApp:
    """法律智能体类案报告生成系统 - GUI应用"""
    
    def __init__(self, root: tk.Tk):
        """初始化GUI应用"""
        self.root = root
        self.root.title("法律智能体类案报告生成系统")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 文件路径
        self.file_path: Optional[str] = None
        
        # 初始化智能体（延迟加载）
        self.forum_agent: Optional[ForumAgent] = None
        self.report_agent: Optional[ReportAgent] = None
        
        # 创建界面
        self._create_widgets()
        
        logger.info("GUI应用初始化完成")
    
    def _create_widgets(self):
        """创建GUI组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="律镜",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件上传（可选）", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="选择文件（可选）:").grid(row=0, column=0, padx=(0, 10))
        
        self.file_path_var = tk.StringVar(value="未选择文件")
        file_path_label = ttk.Label(
            file_frame,
            textvariable=self.file_path_var,
            foreground="gray"
        )
        file_path_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        file_button = ttk.Button(
            file_frame,
            text="浏览...",
            command=self._select_file
        )
        file_button.grid(row=0, column=2)
        
        # 问题输入区域
        question_frame = ttk.LabelFrame(main_frame, text="问题输入", padding="10")
        question_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        question_frame.columnconfigure(0, weight=1)
        
        ttk.Label(
            question_frame,
            text="请输入您的问题或需求:"
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.question_text = scrolledtext.ScrolledText(
            question_frame,
            height=5,
            wrap=tk.WORD
        )
        self.question_text.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 提交按钮区域（放在问题输入框下方，更明显）
        button_frame = ttk.LabelFrame(main_frame, text="操作", padding="10")
        button_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 10))
        button_frame.columnconfigure(0, weight=1)
        
        # 创建按钮容器，居中显示
        button_container = ttk.Frame(button_frame)
        button_container.grid(row=0, column=0)
        
        # 使用更大的按钮样式
        style = ttk.Style()
        style.configure("Large.TButton", font=("Arial", 11, "bold"), padding=10)
        
        self.submit_button = ttk.Button(
            button_container,
            text="🚀 生成报告",
            command=self._submit_request,
            state="normal",
            style="Large.TButton",
            width=25
        )
        self.submit_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.save_button = ttk.Button(
            button_container,
            text="💾 保存报告",
            command=self._save_report,
            state="disabled",
            style="Large.TButton",
            width=25
        )
        self.save_button.pack(side=tk.LEFT)
        
        # 进度显示
        self.progress_var = tk.StringVar(value="就绪")
        progress_label = ttk.Label(
            main_frame,
            textvariable=self.progress_var,
            foreground="blue"
        )
        progress_label.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        # 结果展示区域
        result_frame = ttk.LabelFrame(main_frame, text="报告结果", padding="10")
        result_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=("Consolas", 10)
        )
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 保存的报告内容
        self.current_report: Optional[str] = None
    
    def _select_file(self):
        """选择文件"""
        file_path = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[
                ("Word文档", "*.docx *.doc"),
                ("PDF文档", "*.pdf"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.file_path = file_path
            file_name = Path(file_path).name
            self.file_path_var.set(f"已选择: {file_name}")
            logger.info(f"选择文件: {file_name}")
    
    def _submit_request(self):
        """提交请求"""
        # 检查问题输入（文件是可选的）
        question = self.question_text.get("1.0", tk.END).strip()
        if not question:
            messagebox.showerror("错误", "请输入您的问题或需求")
            return
        
        # 禁用提交按钮
        self.submit_button.config(state="disabled")
        self.save_button.config(state="disabled")
        
        # 清空结果
        self.result_text.delete("1.0", tk.END)
        self.current_report = None
        
        # 在新线程中处理请求
        thread = threading.Thread(target=self._process_request, args=(question,))
        thread.daemon = True
        thread.start()
    
    def _process_request(self, question: str):
        """处理请求（在后台线程中运行）"""
        try:
            # 更新进度
            self._update_progress("正在初始化智能体...")
            
            # 初始化智能体（如果未初始化）
            if self.forum_agent is None:
                self._update_progress("正在初始化论坛智能体...")
                self.forum_agent = ForumAgent(max_rounds=10)
            
            if self.report_agent is None:
                self._update_progress("正在初始化报告智能体...")
                self.report_agent = ReportAgent()
            
            # 读取文件内容（如果提供了文件）
            file_content = None
            if self.file_path and os.path.exists(self.file_path):
                self._update_progress("正在读取文件内容...")
                try:
                    file_content = self._read_file_content(self.file_path)
                    if not file_content or not file_content.strip():
                        logger.warning("文件内容为空，将仅使用问题输入")
                        file_content = None
                except Exception as e:
                    logger.warning(f"读取文件失败: {e}，将仅使用问题输入")
                    file_content = None
            
            # 构建用户需求（文件内容 + 用户问题，或仅用户问题）
            if file_content:
                user_requirement = f"""
文件内容：
{file_content}

用户问题：
{question}
"""
            else:
                user_requirement = question
            
            # 执行论坛辩论
            self._update_progress("正在进行智能体辩论（这可能需要几分钟）...")
            forum_result = self.forum_agent.conduct_debate(user_requirement)
            
            # 生成报告
            self._update_progress("正在生成报告...")
            report_result = self.report_agent.generate_report(forum_result)
            
            # 转换为Markdown格式
            self._update_progress("正在格式化报告...")
            markdown_content = self._format_to_markdown(report_result)
            
            # 显示结果
            self.current_report = markdown_content
            self.root.after(0, self._display_result, markdown_content)
            self.root.after(0, lambda: self._update_progress("报告生成完成！"))
            self.root.after(0, lambda: self.save_button.config(state="normal"))
            
        except Exception as e:
            error_msg = f"处理请求时发生错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.root.after(0, lambda: self._update_progress(f"错误: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            self.root.after(0, lambda: self.submit_button.config(state="normal"))
    
    def _read_file_content(self, file_path: str) -> str:
        """读取文件内容"""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.docx':
                return self._read_docx(file_path)
            elif file_ext == '.doc':
                return self._read_doc(file_path)
            elif file_ext == '.pdf':
                return self._read_pdf(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise
    
    def _read_docx(self, file_path: str) -> str:
        """读取Word文档（.docx）"""
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(paragraphs)
        except ImportError:
            raise ImportError("需要安装 python-docx 库: pip install python-docx")
        except Exception as e:
            raise ValueError(f"读取Word文档失败: {e}")
    
    def _read_doc(self, file_path: str) -> str:
        """读取Word文档（.doc）"""
        # 尝试多种方法
        errors = []
        
        # 方法1: 使用 win32com (Windows)
        if os.name == 'nt':
            try:
                import win32com.client
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                doc = word.Documents.Open(os.path.abspath(file_path))
                text = doc.Content.Text
                doc.Close()
                word.Quit()
                return text
            except Exception as e:
                errors.append(f"win32com: {e}")
        
        # 方法2: 使用 textract
        try:
            import textract
            text = textract.process(file_path).decode('utf-8')
            if text.strip():
                return text
        except Exception as e:
            errors.append(f"textract: {e}")
        
        raise ValueError(f"无法读取.doc文件。错误: {'; '.join(errors)}")
    
    def _read_pdf(self, file_path: str) -> str:
        """读取PDF文档"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except ImportError:
            raise ImportError("需要安装 PyPDF2 库: pip install PyPDF2")
        except Exception as e:
            raise ValueError(f"读取PDF文档失败: {e}")
    
    def _format_to_markdown(self, report_result: Dict[str, Any]) -> str:
        """将报告结果格式化为Markdown"""
        # 优先使用格式化文本（如果存在）
        formatted_text = report_result.get("formatted_text", "")
        if formatted_text:
            return formatted_text
        
        # 如果没有格式化文本，从结构化数据生成
        structured_report = report_result.get("structured_report", {})
        report = structured_report.get("report", {})
        metadata = report_result.get("metadata", {})
        
        # 构建Markdown内容
        markdown_lines = []
        
        # 标题
        title = report.get("title", "法律分析报告")
        markdown_lines.append(f"# {title}\n\n")
        
        # 分析报告（这是主体内容）
        analysis_report = report.get("analysis_report", "")
        if analysis_report:
            markdown_lines.append(f"{analysis_report}\n\n")
        
        # 支撑法律条文（作为附录，支撑分析报告中的观点）
        supporting_laws = report.get("supporting_laws", [])
        if supporting_laws:
            markdown_lines.append("---\n\n")
            markdown_lines.append("## 支撑法律条文\n\n")
            markdown_lines.append("以下法律条文作为上述分析报告的支撑依据：\n\n")
            for i, law in enumerate(supporting_laws, 1):
                law_name = law.get("law_name", "")
                article_number = law.get("article_number", "")
                article_content = law.get("article_content", "")
                how_it_supports = law.get("how_it_supports", "")
                
                if law_name and article_number:
                    markdown_lines.append(f"### {i}. {law_name} 第{article_number}条\n\n")
                
                if article_content:
                    markdown_lines.append(f"**条文内容**：{article_content}\n\n")
                
                if how_it_supports:
                    markdown_lines.append(f"**如何支撑分析**：{how_it_supports}\n\n")
                
                markdown_lines.append("---\n\n")
        
        return "".join(markdown_lines)
    
    def _display_result(self, content: str):
        """显示结果"""
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", content)
    
    def _update_progress(self, message: str):
        """更新进度信息"""
        self.progress_var.set(message)
        logger.info(message)
    
    def _save_report(self):
        """保存报告"""
        if not self.current_report:
            messagebox.showwarning("警告", "没有可保存的报告")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存报告",
            defaultextension=".md",
            filetypes=[
                ("Markdown文件", "*.md"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_report)
                messagebox.showinfo("成功", f"报告已保存到: {file_path}")
                logger.info(f"报告已保存: {file_path}")
            except Exception as e:
                error_msg = f"保存报告失败: {str(e)}"
                messagebox.showerror("错误", error_msg)
                logger.error(error_msg)


def main():
    """主函数"""
    # 创建GUI应用
    root = tk.Tk()
    app = LegalReportApp(root)
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()

