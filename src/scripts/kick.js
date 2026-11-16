const utils = require('./utils');

if (process.argv.length < 4) {
    utils.coloredText('Usage: node kick.js <host> <port> <username> <version> [<proxyFile>]');
    process.exit(1);
}

const host = process.argv[2];
const port = process.argv[3];
const username = process.argv[4];
const version = process.argv[5];
const spaces = process.argv[6];
const proxyFile = process.argv[7];

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

function createBot(proxy = null) {
    let bot;

    try {
        bot = utils.createBotInstance({
            host,
            port,
            username,
            version,
            proxy,
            onProxyError: (err) => {
                utils.coloredText('§cProxy Error');
                utils.coloredText(err);
            }
        });
    } catch (error) {
        utils.handleBotCreationError(error, spaces);
        process.exit(1);
    }

    bot.on('login', () => {
        utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] §aThe user ${username} was successfully kicked from the server.`);
        bot.quit();
        process.exit(1);
    });

    bot.on('kicked', (reason) => {
        const message = utils.formatKickReason(reason).replace(/\s{2,}/g, ' ').replace(/\n/g, ' ');
        utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] The bot was unable to connect to the server due to the following reason: ${message}`);
        bot.quit();
        process.exit(1);
    });

    bot.on('error', (err) => {
        utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] The bot was unable to connect to the server due to the following reason: ${err}`);
        bot.quit();
        process.exit(1);
    });

    setTimeout(() => {
        utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] The bot was unable to connect to the server due to the following reason: §cTimeout`);
        bot.quit();
        process.exit(1);
    }, 10000);
}

if (proxyFile) {
    const randomProxy = utils.getProxy(proxyFile);

    if (randomProxy) {
        createBot(randomProxy);
    } else {
        utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] Invalid Proxy: ${proxyFile}`);
    }
} else {
    createBot();
}
