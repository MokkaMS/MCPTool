const fs = require('fs');
const mccolors = require('minecraft-colors');
const mineflayer = require('mineflayer');
const minecraftData = require('minecraft-data');
const nbt = require('prismarine-nbt');
const { ProxyAgent } = require('proxy-agent');
const socks = require('socks').SocksClient;


function extractTextFromComponent(node) {
    if (node === null || node === undefined) {
        return '';
    }

    if (typeof node === 'string' || typeof node === 'number' || typeof node === 'boolean') {
        return String(node);
    }

    if (Array.isArray(node)) {
        return node.map(extractTextFromComponent).join('');
    }

    if (typeof node === 'object') {
        // Unwrap prismarine-nbt anonymousNbt / NBT compound structures (1.20.3+)
        if (typeof node.type === 'string' && 'value' in node) {
            try {
                return extractTextFromComponent(nbt.simplify(node));
            } catch (_) {}
        }

        let text = '';

        if (node.text !== undefined && node.text !== null) {
            text += String(node.text);
        } else if (node[''] !== undefined && node[''] !== null) {
            text += String(node['']);
        }

        if (node.translate !== undefined && node.translate !== null) {
            text += String(node.translate);
        }

        if (node.extra !== undefined && node.extra !== null) {
            text += extractTextFromComponent(node.extra);
        }

        if (node.with !== undefined && node.with !== null) {
            text += extractTextFromComponent(node.with);
        }

        return text;
    }

    return '';
}


function getTextFromJSON(json) {
    if (json === null || json === undefined) {
        return '';
    }

    if (typeof json === 'object') {
        return extractTextFromComponent(json).trim();
    }

    if (typeof json !== 'string') {
        return String(json).trim();
    }

    try {
        const obj = JSON.parse(json);
        return extractTextFromComponent(obj).trim();
    } catch (_) {
        return json.trim();
    }
}

function formatKickReason(reason) {
    const message = getTextFromJSON(reason);
    if (message.length > 0) {
        return message;
    }

    if (typeof reason === 'string') {
        return reason;
    }

    try {
        return JSON.stringify(reason);
    } catch (_) {
        return String(reason);
    }
}

function normalizeVersion(version) {
    if (version === false || version === undefined || version === null) {
        return false;
    }

    const str = String(version).trim();
    if (!str || str.toLowerCase() === 'auto' || str.toLowerCase() === 'false') {
        return false;
    }

    if (minecraftData(str)) {
        return str;
    }

    if (/^\d+\.\d+\.0$/.test(str)) {
        const withoutPatch = str.slice(0, -2);
        if (minecraftData(withoutPatch)) {
            return withoutPatch;
        }
    }

    return str;
}

function createBotInstance({ host, port, username, version, proxy = null, connectTimeout = null, onProxyError = null }) {
    const parsedPort = parseInt(port, 10);
    const resolvedVersion = normalizeVersion(version);

    if (proxy) {
        const socksOptions = {
            proxy: {
                host: proxy[0],
                port: proxy[1],
                type: 5
            },
            command: 'connect',
            destination: {
                host: host,
                port: parsedPort
            }
        };

        if (connectTimeout != null) {
            socksOptions.timeout = connectTimeout;
        }

        return mineflayer.createBot({
            connect: client => {
                socks.createConnection(socksOptions, (err, info) => {
                    if (err) {
                        if (onProxyError) {
                            onProxyError(err);
                        }
                        return;
                    }

                    client.setSocket(info.socket);
                    client.emit('connect');
                });
            },
            agent: new ProxyAgent({ protocol: 'socks5:', host: proxy[0], port: proxy[1] }),
            username: username,
            fakeHost: host,
            version: resolvedVersion,
            hideErrors: true
        });
    }

    return mineflayer.createBot({
        host: host,
        fakeHost: host,
        port: parsedPort,
        username: username,
        version: resolvedVersion,
        hideErrors: true
    });
}

function handleBotCreationError(error, spaces) {
    const msg = error && error.message ? error.message : String(error);

    if (msg.includes('is not supported')) {
        const versionMatch = msg.match(/\d+\.\d+(?:\.\d+)?/) || msg.match(/'([^']+)'/);
        const versionText = versionMatch ? (versionMatch[1] || versionMatch[0]) : 'unknown';
        coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] §cIncompatible Minecraft version: Version §c§l${versionText} §cis not currently supported.`);
    } else if (msg.includes('unsupported protocol version:') || msg.includes('unsupported/unknown protocol version:')) {
        let protocol = null;
        try {
            const splitPart = msg.split(': ')[1];
            protocol = splitPart ? splitPart.split(',')[0].trim() : null;
        } catch (_) {
            const numMatch = msg.match(/\d+/);
            protocol = numMatch ? numMatch[0] : null;
        }

        if (protocol != null && protocol !== '') {
            coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] §cIncompatible Minecraft version: Protocol §c§l${protocol} §cis not supported`);
        } else {
            coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] §cIncompatible Minecraft version: Protocol is not supported`);
        }
    } else {
        coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] §4Error`);
    }
}

function coloredText(text) {
    console.log(mccolors.translateColors(text));
}

function checkLogsDirectory(directory) {
    const logsDir = directory;
  
    if (!fs.existsSync(logsDir)) {
        fs.mkdirSync(logsDir, { recursive: true });
    }
}

function generateFilename(name) {
    const date = new Date();
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString();
    const hour = date.getHours().toString().padStart(2, '0');
    const minute = date.getMinutes().toString().padStart(2, '0');
    const second = date.getSeconds().toString().padStart(2, '0');
    const filename = `${name}_${day}-${month}-${year}_${hour}.${minute}.${second}.txt`;

    if (fs.existsSync(filename)) {
        return generateFilename(name);
    }

    return filename;
}

function readFile(commandFile) {
    try {
        const fileContent = fs.readFileSync(commandFile, 'utf8');
        return fileContent.split(/\r?\n/).map(word => word.trim());
    } catch (err) {
        return null;
    }
}

function getMessages(file) {
    try {        
        const messagesFile = fs.readFileSync(file, 'utf8');
        const messagesList = messagesFile.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 0);

        if (messagesList.length >= 1) {
            return messagesList;
        }
                
        return null;
    } catch(_) {}
    return null;
}


function getProxy(file) {
    try {        
        const proxyFile = fs.readFileSync(file, 'utf8');
        const proxyList = proxyFile.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 0);

        if (proxyList.length >= 1) {
            let randomProxy = proxyList[Math.floor(Math.random() * proxyList.length)].replace(/\s+/g, '');
            randomProxy = randomProxy.split(':');
            return [randomProxy[0], parseInt(randomProxy[1])];
        }
                
        return null;
    } catch(_) {}
    return null;
}


function getUsername(file) {
    try {        
        const usernameFile = fs.readFileSync(file, 'utf8');
        const usernameList = usernameFile.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 0);

        if (usernameList.length >= 1) {
            return usernameList[Math.floor(Math.random() * usernameList.length)].replace(/\s+/g, '');
        }
                
        return null;
    } catch(_) {}
    return null;
}


function getListOfPasswords(file){
    try {
        const passwordFile = fs.readFileSync(file, 'utf8');
        const passwordList = passwordFile.split(/\r?\n/).map(s => s.trim()).filter(s => s.length > 0);

        if (passwordList.length >= 1) {
            return passwordList;
        }

        return null;
    } catch (_) {
        return null;
    }
}

function getSpaces(spaces) {
    return ' '.repeat(parseInt(spaces) || 0);
}


async function tab(bot, text, returnResults=false) {
    try {
        let matches = await bot.tabComplete(text);

        if (Array.isArray(matches)) {
            matches = matches.map(obj => (typeof obj === 'object' && obj !== null) ? obj.match : obj).filter(Boolean);
        } else {
            matches = [];
        }
        
        if (returnResults === true) {
            return matches;
        }

        coloredText(matches.join(', '));
        
    } catch (err) {
        if (returnResults === true) {
            return [];
        }
    }
}

module.exports = {
    getTextFromJSON: getTextFromJSON,
    formatKickReason: formatKickReason,
    normalizeVersion: normalizeVersion,
    createBotInstance: createBotInstance,
    handleBotCreationError: handleBotCreationError,
    getMessages: getMessages,
    coloredText: coloredText,
    checkLogsDirectory: checkLogsDirectory,
    generateFilename: generateFilename,
    readFile: readFile,
    getListOfPasswords: getListOfPasswords,
    getUsername: getUsername,
    getProxy: getProxy,
    getSpaces: getSpaces,
    tab: tab
};
