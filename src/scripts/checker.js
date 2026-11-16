const utils = require('./utils');

if (process.argv.length < 4) {
    console.log('Usage: node checker.js <host> <port> <version> [<proxyFile>]');
    process.exit(1);
}

const username = utils.getUsername('src/utilities/usernames.txt');
const host = process.argv[2];
const port = process.argv[3];
const version = process.argv[4];
const proxyFile = process.argv[5];
const spaces = 0;

if (proxyFile) {
    let proxyTest = utils.getListOfPasswords(proxyFile);

    if (proxyTest === null) {
        utils.coloredText(`\n${utils.getSpaces(spaces)}§f[§c#§f] §fThe entered proxy file (§c${proxyFile}§f) is not valid.`);
        process.exit(1);
    }
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
                console.log('§cProxy Error');
                console.log(err);
            }
        });
    } catch (error) {
        utils.handleBotCreationError(error, spaces);
        process.exit(1);
    }

    bot.on('login', () => {
        console.log('§aConnected');
        bot.quit();
        process.exit(1);
    });

    bot.on('kicked', (reason) => {
        console.log(utils.formatKickReason(reason));
        bot.quit();
        process.exit(1);
    });

    bot.on('error', (_) => {
        console.log('§cTimeout');
        bot.quit();
        process.exit(1);
    });

    setTimeout(() => {
        console.log('§cTimeout');
        bot.quit();
        process.exit(1);
    }, 10000);
}

if (proxyFile) {
    const randomProxy = utils.getProxy(proxyFile);

    if (randomProxy) {
        createBot(randomProxy);
    } else {
        utils.coloredText(`\n${utils.getSpaces(spaces)}§f§l[§c§l#§f§l] Invalid Proxy: ${proxyFile}`);
    }
} else {
    createBot();
}
