"""Authenticated examples and shareable Chinese exports for Gradio's MCP docs."""

MCP_DOCS_JS = r"""
    const exampleAuthorization = 'Bearer <你的连接密钥>';
    function authenticatedExample(text) {
        let config;
        try { config = JSON.parse(text); } catch { return null; }
        if (!config || typeof config.mcpServers !== 'object' || !config.mcpServers) return null;
        let found = false;
        for (const service of Object.values(config.mcpServers)) {
            if (!service || typeof service !== 'object') continue;
            if (typeof service.url === 'string' && service.url.includes('/gradio_api/mcp')) {
                service.headers = {...service.headers, Authorization: exampleAuthorization};
                found = true;
            } else if (Array.isArray(service.args) && service.args.includes('mcp-remote')
                       && service.args.some(arg => typeof arg === 'string' && arg.includes('/gradio_api/mcp'))) {
                // Replace an existing auth example, or append the missing request header.
                const args = service.args;
                const transportIndex = args.indexOf('--transport');
                if (transportIndex >= 0 && args[transportIndex + 1] === 'streamable-http') {
                    args[transportIndex + 1] = 'http-only';
                }
                if (service.command === 'npx' && !args.includes('--yes') && !args.includes('-y')) args.unshift('--yes');
                let replaced = false;
                for (let i = 0; i < args.length - 1; i++) {
                    if (args[i] === '--header' && /^Authorization\s*:/i.test(args[i + 1])) {
                        args[i + 1] = 'Authorization: ' + exampleAuthorization;
                        replaced = true;
                    }
                }
                if (!replaced) args.push('--header', 'Authorization: ' + exampleAuthorization);
                found = true;
            }
        }
        return found ? config : null;
    }
    function activeMCPDialog() {
        return [...document.querySelectorAll('[role="dialog"]')].find(dialog =>
            dialog.querySelector('.transport-selection')?.checkVisibility());
    }
    function enhanceMCPDocs() {
        const dialog = activeMCPDialog();
        if (!dialog) return;
        for (const pre of dialog.querySelectorAll('pre')) {
            const config = authenticatedExample(pre.textContent);
            if (!config) continue;
            const next = JSON.stringify(config, null, 2);
            // Keep the framework's text node so changing tool selection still updates examples.
            if (pre.textContent !== next && pre.childNodes.length === 1
                    && pre.firstChild.nodeType === Node.TEXT_NODE) pre.firstChild.nodeValue = next;
        }
    }
    async function mcpMarkdown(dialog) {
        const examples = {};
        for (const pre of dialog.querySelectorAll('pre')) {
            const config = authenticatedExample(pre.textContent);
            if (!config) continue;
            const direct = Object.values(config.mcpServers).some(service => service?.url?.includes('/gradio_api/mcp'));
            examples[direct ? 'http' : 'stdio'] = config;
        }
        if (!examples.http || !examples.stdio) throw new Error('连接示例尚未加载');
        const address = dialog.querySelector('#mcp-server-url')?.value
            || Object.values(examples.http.mcpServers).find(service => service?.url?.includes('/gradio_api/mcp'))?.url;
        if (!address) throw new Error('MCP 地址尚未加载');
        const schemaURL = new URL(address, window.location.href);
        schemaURL.pathname = schemaURL.pathname.replace(/\/$/, '') + '/schema';
        const response = await fetch(schemaURL, {credentials: 'same-origin'});
        if (!response.ok) throw new Error('工具说明尚未加载');
        const schema = await response.json();
        const selected = new Set([...dialog.querySelectorAll('.tool-item')]
            .filter(item => !item.querySelector('.tool-checkbox') || item.querySelector('.tool-checkbox').checked)
            .map(item => item.querySelector('.tool-name')?.textContent.trim()));
        const tools = schema.filter(tool => selected.has(tool.name));
        const fence = config => '```json\n' + JSON.stringify(config, null, 2) + '\n```';
        const types = {string:'字符串', boolean:'布尔值', number:'数字', integer:'整数', object:'对象', array:'数组'};
        const lines = [
            '# 深度视频转换器 MCP 使用文档', '',
            'MCP 服务地址：' + address, '',
            '## 连接方法', '',
            '1. 在网页“设置 → AI 连接”中打开“允许 AI 助手连接”。',
            '2. 点击“复制连接配置”，将包含真实地址和密钥的完整配置添加到 AI 客户端。',
            '3. 客户端需支持 Streamable HTTP 和 Authorization 请求头；网页中的“测试连接”可检查服务是否正常。', '',
            '以下内容是可分享的说明文档，不包含真实连接密钥。示例中的 <你的连接密钥> 需要替换；也可直接使用网页的“复制连接配置”。', '',
            '当前版本在同一服务内共用一把密钥，尚未提供网站用户账号和每人独立密钥。', '',
            '127.0.0.1 仅代表客户端所在的电脑。服务器部署需另行配置公网域名、HTTPS 和访问权限。', '',
            '## 流式 HTTP（Streamable HTTP）', '', fence(examples.http), '',
            '## 标准输入输出（STDIO）', '',
            '仅支持 STDIO 的客户端，可先安装 Node.js，再通过 mcp-remote 转接。下方 --header 参数用于传递连接密钥。', '',
            fence(examples.stdio), '',
            '## 可用工具', '', '工具数量：' + tools.length, ''
        ];
        for (const tool of tools) {
            const parameters = tool.inputSchema?.properties || {};
            const required = new Set(tool.inputSchema?.required || []);
            lines.push('### ' + tool.name, '', '类型：工具',
                '说明：' + translate(tool.description || '此工具尚未提供说明。'),
                '参数数量：' + Object.keys(parameters).length, '');
            for (const [name, parameter] of Object.entries(parameters)) {
                const type = types[parameter.type] || parameter.type || '未指定';
                const defaultValue = 'default' in parameter ? '；默认值：' + JSON.stringify(parameter.default) : '';
                lines.push('- `' + name + '`（' + type + '，' + (required.has(name) ? '必填' : '选填') + defaultValue
                    + '）：' + translate(parameter.description || '暂无说明。'));
            }
            lines.push('');
        }
        lines.push('## 视频文件上传', '',
            '先将视频上传到应用，再将上传工具返回的文件路径或可访问的视频 URL 交给转换工具。');
        if (examples.http.mcpServers.upload_files_to_gradio) {
            lines.push('示例已包含 `upload_files_to_gradio` 文件上传工具。请安装 uv，并将 `<UPLOAD_DIRECTORY>` 替换为本机的视频目录。');
        } else {
            lines.push('当前示例未包含文件上传工具。客户端需要自行上传文件；也可在文档面板勾选“包含 Gradio 文件上传工具”。');
        }
        lines.push('', '更多说明：[Gradio MCP 文档](https://www.gradio.app/guides/building-mcp-server-with-gradio)。');
        return lines.join('\n');
    }
    document.addEventListener('click', async event => {
        const dialog = activeMCPDialog();
        const button = event.target.closest('button');
        if (!dialog || !button || !dialog.contains(button)) return;
        const pre = button.closest('code')?.querySelector('pre');
        const example = pre && authenticatedExample(pre.textContent);
        const pageCopy = button.matches('.container-wrapper .trigger-wrapper > .copy-button')
            || (button.getAttribute('role') === 'menuitem'
                && /^(复制页面|已复制说明文档)$/.test(button.querySelector('.menu-text-primary')?.textContent.trim()));
        if (!example && !pageCopy) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        try {
            const text = example ? JSON.stringify(example, null, 2) : await mcpMarkdown(dialog);
            await navigator.clipboard.writeText(text);
            if (pageCopy) {
                const label = button.querySelector('.menu-text-primary') || button.querySelector('span:last-child');
                if (label) label.textContent = '已复制说明文档';
            }
            button.setAttribute('title', example ? '已复制示例，需填写连接密钥' : '已复制说明文档，不含真实密钥');
            button.setAttribute('aria-label', example ? '已复制示例，需填写连接密钥' : '已复制说明文档，不含真实密钥');
        } catch {
            button.setAttribute('title', '复制失败，请等待页面加载完成后重试');
            button.setAttribute('aria-label', '复制失败，请等待页面加载完成后重试');
        }
    }, true);
"""
