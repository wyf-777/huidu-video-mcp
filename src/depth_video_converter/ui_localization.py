"""Translate Gradio's hard-coded chrome without changing API identifiers or code."""

from .mcp_docs_ui import MCP_DOCS_JS

LOCALIZE_JS = r"""() => {
    if (window.__depthChineseUI) return;
    window.__depthChineseUI = true;
    const translations = new Map(Object.entries({
        'API Docs': 'API 接口文档',
        'API Documentation': 'API 接口文档',
        'documentation': '接口文档',
        'API endpoint': '个 API 接口',
        'endpoint': '个接口',
        'API Recorder': 'API 调用录制',
        'Recording API Calls:': '正在录制 API 调用：',
        'CLI': '命令行（CLI）',
        'CLI endpoint': '个命令行接口',
        'Gradio CLI': 'Gradio 命令行',
        'HF CLI': 'Hugging Face 命令行',
        'MCP Tool': '个 MCP 工具',
        'MCP Tools': '个 MCP 工具',
        'Transport:': '传输方式：',
        'Streamable HTTP': '流式 HTTP（Streamable HTTP）',
        'STDIO': '标准输入输出（STDIO）',
        'MCP Server URL (Streamable HTTP)': 'MCP 服务地址（流式 HTTP）',
        'Select All': '全选',
        'Select None': '取消全选',
        '), Resources (': '）、资源（',
        '), and Prompts (': '）和提示词（',
        'Streamable HTTP Transport': '流式 HTTP 连接方式',
        ': To add this MCP to clients that support Streamable HTTP, simply add the following configuration to your MCP config.': '：客户端支持 Streamable HTTP 时，可使用下方配置格式。实际连接请从“设置 → AI 连接”复制含密钥的完整配置。',
        'STDIO Transport': '标准输入输出连接方式',
        ': For clients that only support stdio (e.g. Claude Desktop), first': '：如果客户端仅支持标准输入输出（STDIO），请先',
        'install Node.js': '安装 Node.js',
        '. Then, you can use the following command:': '，然后使用下方命令。连接本应用时，还需配置“AI 连接”中提供的密钥。',
        'Include Gradio file upload tool': '包含 Gradio 文件上传工具',
        'tool uploads files from your local': '会将本机目录',
        '(or any of its subdirectories) to the Gradio app. This is needed because MCP servers require files to be provided as URLs. You can omit this tool if you prefer to upload files manually. This tool requires': '及其子目录中的文件上传到应用。MCP 服务需要通过 URL 接收文件；如果自行上传文件，可以不包含此工具。使用该工具需要先安装',
        'to be installed.': '。',
        'Read more about MCP in the Gradio docs': '在 Gradio 文档中了解更多 MCP 用法',
        '⚠︎ No description for this parameter in function docstring': '⚠︎ 此参数尚未提供说明',
        '⚠︎ No description provided in function docstring': '⚠︎ 此工具尚未提供说明',
        'Making a prediction and getting a result requires': '调用接口并取得结果需要',
        '2 requests': '发送两次请求',
        ': a': '：先发送',
        'and a': '，再发送',
        'request. The': '请求。首次',
        'request returns an': '请求会返回',
        ', which is used in the second': '，第二次',
        "request to fetch the results. In these snippets, we've used": '请求使用它获取结果。下方示例使用',
        'to parse the results, combining these two requests into one command for ease of use.': '解析结果，将两次请求合并为一条命令，方便调用。',
        'If your endpoint accepts files, you must first upload them via a': '如果接口接收文件，请先通过',
        ', then reference the returned path with the': '，再将返回的文件路径与以下字段一起传入：',
        'key:': '，格式如下：',
        'curl docs': 'cURL 使用文档',
        'Stop Recording': '停止录制',
        'Start Recording': '开始录屏',
        'Screen Studio': '屏幕录制',
        'BETA': '测试版',
        'beta': '测试版',
        'Progressive Web App is not enabled for this app. To enable it, start your Gradio app with': '此应用尚未启用渐进式 Web 应用。如需启用，启动时设置',
        'Screen Studio allows you to record your screen and generates a video of your app with automatically adding zoom in and zoom out effects as well as trimming the video to remove the prediction time.': '屏幕录制可以录下应用操作，自动添加缩放效果，并剪去等待处理结果的时间。',
        'Start recording by clicking the': '点击下方的',
        'button below and then sharing the current browser tab of your Gradio demo. Use your app as you would normally to generate a prediction.': '按钮，选择共享当前应用所在的浏览器标签页，然后正常操作应用即可。',
        'Stop recording by clicking the': '录制完成后，点击页面底部的',
        'button in the footer of the demo.': '按钮即可停止。',
        'Include automatic zoom in/out': '自动添加放大和缩小效果',
        'Include automatic video trimming': '自动剪去等待时间',
        'Choose where new runs are saved and revisit earlier results.': '选择新运行记录的保存位置，也可以查看以前的结果。',
        'View run history': '查看运行历史',
        'History storage': '历史记录保存位置',
        'This browser': '当前浏览器',
        'Private to this device': '仅保存在此设备',
        'Save new runs to': '将新运行记录保存到',
        'Private and available only on this device': '私密保存，仅当前设备可用',
        'Stored in a Hugging Face bucket': '保存在 Hugging Face 存储桶中',
        'Connect a bucket': '连接存储桶',
        'Change bucket': '更换存储桶',
        'Connect history storage': '连接历史记录存储',
        'Save future runs to a Hub bucket and open them from any browser with access. Runs already stored in this browser stay here.': '将之后的运行记录保存到 Hub 存储桶，可从有访问权限的浏览器中查看。此前保存在当前浏览器的记录仍保留在本机。',
        'Loading your buckets…': '正在加载你的存储桶……',
        'Your buckets': '你的存储桶',
        'or use another bucket': '或使用其他存储桶',
        'Bucket ID': '存储桶标识',
        'New buckets are private by default. Organization buckets are supported.': '新建存储桶默认为私有，也支持组织的存储桶。',
        'Connect': '连接',
        'Connecting…': '正在连接……',
        'Sign in with Hugging Face': '使用 Hugging Face 登录',
        'Log in locally with `hf auth login`, then try again.': '请先在本机运行 `hf auth login` 登录，然后重试。',
        'Could not connect this bucket.': '无法连接此存储桶。',
        'Could not load your buckets.': '无法加载你的存储桶。',
        'Available anywhere you can access this bucket': '可从有权限访问此存储桶的设备查看',
        '🪄 Recorded API Calls': '🪄 已录制的 API 调用',
        'Choose one of the following ways to interact with the API.': '请选择以下一种方式调用 API 接口。',
        '1. Install the': '1. 安装',
        'client (': '客户端（',
        'docs': '使用文档',
        ") if you don't already have it installed.": '），如果已经安装，可跳过此步骤。',
        '2. Find the API endpoint below corresponding to your desired function in the app. Copy the code snippet, replacing the placeholder values with your own input data.': '2. 在下方找到对应功能的 API 接口，复制示例代码，并将示例参数替换为自己的输入数据。',
        'Or use the': '也可以使用',
        'to automatically generate your API requests.': '自动生成 API 请求。',
        'API name:': 'API 名称：',
        'Copy Page': '复制页面',
        'Copy': '复制',
        'Copied!': '已复制！',
        'Copied': '已复制',
        'Copy code': '复制代码',
        'Copy to clipboard': '复制到剪贴板',
        'Copy menu': '复制菜单',
        'Open copy menu': '展开复制菜单',
        'Close copy menu': '收起复制菜单',
        'Open in HuggingChat': '在 HuggingChat 中打开',
        'Required': '必填',
        'Optional': '选填',
        'Default:': '默认值：',
        'Returns': '返回结果：',
        'Takes no input parameters': '无需输入参数',
        'Most recently used': '最近使用',
        'Note: Some API calls only affect the UI, so when using the clients, the desired result may be achieved with only a subset of the recorded calls.': '注意：部分 API 调用只影响界面。使用客户端时，可能只需执行部分录制的调用即可获得所需结果。',
        '1. Confirm that you have cURL installed on your system.': '1. 确认系统已安装 cURL。',
        "1. Install the CLI if you don't already have it installed.": '1. 如果尚未安装，请先安装命令行工具。',
        'First, install the HF CLI.': '首先，安装 Hugging Face 命令行工具。',
        'On macOS and Linux:': '在 macOS 和 Linux 上：',
        'On Windows:': '在 Windows 上：',
        'Then, install the Gradio extension:': '然后，安装 Gradio 扩展：',
        'Settings': '设置',
        'Language': '语言',
        'Display theme': '显示主题',
        'System': '跟随系统',
        'Light': '浅色',
        'Dark': '深色',
        'Close': '关闭',
        'Upload file': '上传文件',
        'File upload': '上传文件',
        'Capture from camera': '使用摄像头录制',
        'Gradio footer navigation': 'Gradio 页脚导航'
    }));
    // These short fragments only occur between inline code in generated docs.
    const docFragments = new Map(Object.entries({
        'The': '工具', 'and': '和', 'See': '参见', 'to': '请求上传至'
    }));
    function translate(value, element) {
        const key = value.trim().replace(/\s+/g, ' ');
        let result = translations.get(key);
        if (result === undefined && element?.closest('[role="dialog"]')) {
            result = docFragments.get(key);
        }
        if (!result) {
            result = key.replace(/^Accepts (\d+) parameters?$/, '接收 $1 个参数')
                .replace(/^(\d+) Available MCP Tools \($/, '$1 个可用 MCP 工具（')
                .replace(/^Accepts a JSON object with (\d+) keys?$/, '接收包含 $1 个字段的 JSON 对象')
                .replace(/^(tuple|list|array) of (\d+) elements$/, '包含 $2 项的$1')
                .replace(/^an array of (\d+) elements?$/, '包含 $1 项的数组')
                .replace(/^1 element$/, '1 项')
                .replace(/^(\(\w+), default: (.*)\)$/, '$1，默认值：$2)')
                .replace(/^(\d+) requests \((\d+)% successful, p50: (.*)\)$/, '$1 次请求（成功率 $2%，中位耗时：$3）')
                .replace(/^You do not have write access to “(.+)”\.$/, '你没有“$1”的写入权限。')
                .replace(/^Run history \((\d+)\)$/, '运行历史（$1）')
                .replace(/^([☀︎⏾🖥︎\s]+)Light$/u, '$1浅色')
                .replace(/^([☀︎⏾🖥︎\s]+)Dark$/u, '$1深色')
                .replace(/^([☀︎⏾🖥︎\s]+)System$/u, '$1跟随系统')
                .replace(/^Copy (.+) Docs as Markdown for LLMs$/, '将 $1 文档复制为 Markdown，供 AI 使用');
            result = result.replace(/^The input value that is provided in the "([^"]+)" \w+ component\./,
                '来自“$1”控件的输入值。')
                .replace(/^The output value that appears in the "([^"]+)" \w+ component\./,
                '显示在“$1”控件中的输出值。')
                .replace(/The FileData class is a subclass[\s\S]*$/, 'FileData 表示上传的文件及其元数据：path 为服务端文件路径，url 为文件地址，size 为字节大小，orig_name 为原始文件名，mime_type 为媒体类型，is_stream 表示是否为流式文件，meta 为内部元数据（请勿修改）。')
                .replace(/If a user passes a file as an input, use the upload_file_to_gradio tool, if present, to upload the file to the gradio app and create a Gradio File Input\. Then use the returned path as the input to the tool\.?/,
                    '如果输入是文件，可使用客户端提供的文件上传工具，将文件上传后再把返回的路径交给此工具。');
            if (result === key) return value;
            result = result.replace('tuple', '元组').replace('list', '列表').replace('array', '数组');
        }
        return value.replace(/\S[\s\S]*\S|\S/, result);
    }
    const excluded = 'pre, code, textarea, input, script, style, [contenteditable="true"]';
    function apply(root) {
        if (root.nodeType === Node.TEXT_NODE) {
            if (!root.parentElement?.closest(excluded)) {
                const pluralSuffix = root.nodeValue === 's' && /个参数|个字段|个.*接口|个 MCP 工具/.test(root.previousSibling?.textContent || '');
                const next = pluralSuffix ? '' : translate(root.nodeValue, root.parentElement);
                if (next !== root.nodeValue) root.nodeValue = next;
            }
            return;
        }
        if (!(root instanceof Element) || root.closest('pre, code, script, style, [contenteditable="true"]')) return;
        for (const element of [root, ...root.querySelectorAll('[title], [aria-label], [alt], [placeholder]')]) {
            if (element.closest('pre, code, script, style, [contenteditable="true"]')) continue;
            for (const attr of ['title', 'aria-label', 'alt', 'placeholder']) {
                const old = element.getAttribute(attr);
                if (old) {
                    const next = translate(old, element);
                    if (next !== old) element.setAttribute(attr, next);
                }
            }
        }
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) apply(walker.currentNode);
    }
    apply(document.body);
    function enhanceSettings() {
        for (const dialog of document.querySelectorAll('[role="dialog"]')) {
            if (dialog.getAttribute('aria-label') !== '设置' || dialog.querySelector('[data-ai-settings-link]')) continue;
            const entry = document.createElement('button');
            entry.dataset.aiSettingsLink = 'true';
            entry.textContent = 'AI 连接（MCP） →';
            entry.style.cssText = 'display:block;padding:12px 18px;margin:16px 0;border:1px solid #666;border-radius:8px;cursor:pointer;color:inherit;background:transparent;font:inherit';
            entry.onclick = () => {
                dialog.querySelector('.backdrop')?.click();
                const panel = document.getElementById('ai-connection-settings');
                const toggle = panel?.querySelector('button');
                const content = panel?.querySelector('[data-testid="accordion-content"]');
                if (toggle && content && getComputedStyle(content).display === 'none') toggle.click();
                panel?.scrollIntoView({behavior:'smooth', block:'start'});
            };
            const host = dialog.querySelector('[role="document"]') || dialog;
            host.insertBefore(entry, host.firstChild);
        }
    }
""" + MCP_DOCS_JS + r"""
    document.addEventListener('click', async (event) => {
        if (!event.target.closest('#copy-ai-config')) return;
        const button = event.target.closest('button');
        const text = document.querySelector('#ai-client-config .cm-content')?.innerText
            || document.querySelector('#ai-client-config textarea')?.value;
        try {
            JSON.parse(text);
            await navigator.clipboard.writeText(text);
            button.textContent = '已复制连接配置';
        } catch {
            button.textContent = '请使用配置框右上角的复制按钮';
        }
    });
    enhanceSettings();
    enhanceMCPDocs();
    new MutationObserver(records => {
        for (const record of records) {
            if (record.type === 'childList') record.addedNodes.forEach(apply);
            else apply(record.target);
        }
        enhanceSettings();
        enhanceMCPDocs();
    }).observe(document.body, {subtree: true, childList: true, characterData: true,
        attributes: true, attributeFilter: ['title', 'aria-label', 'alt', 'placeholder']});
}"""
