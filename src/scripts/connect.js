const readline = require('readline');
const utils = require('./utils');
const fs = require('fs');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

if (process.argv.length < 5) {
    console.log('Usage: node connect.js <host> <port> <username> <version> <spaces> [<proxyFile>]');
    process.exit(1);
}

const host = process.argv[2];
const port = process.argv[3];
const username = process.argv[4];
const version = process.argv[5];
const spaces = process.argv[6];
const proxyFile = process.argv[7];
let bot;

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

const commandsToViewPlugins = ['/bukkit:version ', '/version ', '/bukkit:about ', '/about ', '/bukkit:ver ', '/ver '];
const moveList = ['forward', 'back', 'left', 'right', 'jump', 'sprint', 'sneak'];
const helpMessage = `
${getSpaces(spaces)}§f§lList of available commands (§cBETA§f§l):

${getSpaces(spaces)}§a§l.help §7§l- §f§lShow this help message.
${getSpaces(spaces)}§a§l.move §b§l<movement> §7§l- §f§lExecute a movement of the bot. (forward, back, left, right, jump, sprint, sneak)
${getSpaces(spaces)}§a§l.file §b§l<file> §7§l- §f§lSend a list of messages/commands that get from the specified file
${getSpaces(spaces)}§a§l.players §7§l- §f§lShow information about all players connected to the server.
${getSpaces(spaces)}§a§l.plugins §7§l- §f§lShows the server plugins. (Using the / tab)
${getSpaces(spaces)}§a§l.seen §b§l<file> §f§lGets the IP addresses of users by using the /seen command. (You must specify a file containing the list of players)
${getSpaces(spaces)}§a§l.litebans §7§l- §f§lSave the litebans database (only if it is vulnerable).
${getSpaces(spaces)}§a§l.baltop §b§l<pages> §7§l- §f§lGets the list of players obtained on the /baltop.
`;

function enterCommand() {
    rl.question('', function (text) {
        const words = text.split(' ');
        const command = words[0];

        if (command === '.help') {
            utils.coloredText(helpMessage);
            enterCommand();
            return;
        }

        if (bot) {
            // Execute a movement of the bot.
            if (command === '.move') {
                if (words[1]) {
                    const movement = words[1];

                    if (moveList.includes(movement)) {
                        if (bot.getControlState(movement)) {
                            bot.setControlState(movement, false);
                        } else {
                            bot.setControlState(movement, true);
                        }
                    }
                }

                enterCommand();
                return;
            }

            // Gets the list of players connected to the server.
            if (command === '.players') {
                const players = bot.players;
                console.log('\n   List of connected players:\n');

                Object.keys(players).forEach(function (key) {
                    utils.coloredText(`${getSpaces(spaces)}§f§l${players[key].username} §7(§b${players[key].uuid}§7) §a${players[key].ping}ms§r`);
                });

                console.log('');
                enterCommand();
                return;
            }

            // Runs a list of commands obtained from a file.
            if (command === '.file') {
                setTimeout(async () => {
                    const commands = utils.readFile(`files/${words[1]}`);

                    if (commands) {
                        for (let i = 0; i < commands.length; i++) {
                            await new Promise(resolve => {
                                setTimeout(() => {
                                    if (typeof commands[i] === 'string' && commands[i].length > 0) {
                                        bot.chat(commands[i]);
                                    }
                                    resolve();
                                }, 1000);
                            });
                        }
                    } else {
                        utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] §cFile not found: ${words[1]}`);
                    }
                });

                enterCommand();
                return;
            }

            // Try to get the list of plugins using the / + tab
            if (command === '.plugins') {
                const playersObject = bot.players;
                const players = [];
                let plugins = [];

                Object.keys(playersObject).forEach(function (key) {
                    players.push(playersObject[key].username);
                });

                setTimeout(async () => {
                    for (let i = 0; i < commandsToViewPlugins.length; i++) {
                        await new Promise(resolve => {
                            let output = utils.tab(bot, commandsToViewPlugins[i], true);

                            output.then((outputList) => {
                                if (Array.isArray(outputList) && outputList.length >= 1) {
                                    outputList.forEach((match) => {
                                        if (!plugins.includes(match) && !players.includes(match)) {
                                            plugins.push(match);
                                        }
                                    });
                                }

                                resolve();
                            });
                        });
                    }

                    if (plugins.length >= 1) {
                        plugins = plugins.join('§f§l, §a§l');
                        utils.coloredText(`${getSpaces(spaces)}§f§lPlugin list: §a§l${plugins}`);
                    } else {
                        console.log('Plugins not found.');
                    }
                }, 100);

                enterCommand();
                return;
            }

            // Extract the players obtained from the /baltop command.
            if (command === '.baltop') {
                const pages = words[1];
                const fileName = utils.generateFilename('Baltop');
                let messages;
                let fileContent;
                let usernames = [];
                let baltopMessages = [];

                bot.chat('/baltop');
                bot.on('message', (message) => {
                    baltopMessages.push(message.toString());
                });

                function onMessage(message) {
                    messages.push(message.toString());
                }

                setTimeout(async () => {
                    if (baltopMessages.some(element => element.includes('$'))) {
                        bot.on('message', onMessage);

                        for (let i = 1; i <= parseInt(pages); i++) {
                            await new Promise(resolve => {
                                bot.chat(`/baltop ${i}`);
                                messages = [];

                                setTimeout(() => {
                                    if (messages.some(element => element.includes('$'))) {
                                        messages.forEach((message) => {
                                            if (message.includes('$') && (!message.includes('Total:'))) {
                                                message = message.split(' ');
                                                let username = message[1];
                                                username = username.replace(',', '');
                                                usernames.push(username);
                                            }
                                        });
                                    } else {
                                        i = parseInt(pages);
                                    }

                                    resolve();
                                }, 1000);
                            });
                        }

                        utils.checkLogsDirectory('./logs/Connect');
                        fileContent = `List of users found in /baltop (${host}:${port}):\n\n${usernames.join('\n')}`;

                        fs.writeFile(`./logs/Connect/${fileName}`, fileContent, (err) => {
                            if (err) {}
                            utils.coloredText(`\n${getSpaces(spaces)}§f§lList of users saved in: §a§l/logs/Connect/${fileName}`);
                        });
                    } else {
                        console.log('No permissions.');
                    }
                }, 1000);

                bot.off('message', onMessage);
                enterCommand();
                return;
            }

            if (command === '.exit') {
                bot.quit();
                rl.close();
                return;
            } else {
                if (text.endsWith(' ')) {
                    utils.tab(bot, text);
                } else {
                    bot.chat(text);
                }
            }

            enterCommand();
        }
    });
}

function createBot(proxy = null) {
    try {
        bot = utils.createBotInstance({
            host,
            port,
            username,
            version,
            proxy,
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
        utils.coloredText(`\n${getSpaces(spaces)}§f§l[§a§l+§f§l] The bot has successfully connected to §a§l${host}:${parseInt(port)}.\n`);
    });

    bot.on('message', (message) => {
        let serverMessage = message.toAnsi();
        console.log(`${getSpaces(spaces)}${serverMessage}`);
    });

    bot.on('kicked', (reason) => {
        const message = utils.formatKickReason(reason).replace(/\s{2,}/g, ' ').replace(/\n/g, ' ');
        utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] The bot was kicked for the following reason: ${message}`);
        bot.quit();
        process.exit(1);
    });

    bot.on('error', (err) => {
        utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] The bot was kicked for the following reason: ${err}`);
        bot.quit();
        process.exit(1);
    });
}

function sendBot() {
    if (proxyFile) {
        const randomProxy = utils.getProxy(proxyFile);

        if (randomProxy) {
            utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §aSending the bot to the server.. §f§l(§d${randomProxy[0]}:${randomProxy[1]}§f§l)`);
            enterCommand();
            createBot(randomProxy);
        } else {
            utils.coloredText(`\n${getSpaces(spaces)}§f§l[§c§l#§f§l] Invalid Proxy: ${proxyFile}`);
        }
    } else {
        utils.coloredText(`\n${getSpaces(spaces)}§f[§c#§f] §aSending the bot to the server.. §f§l(§cNo proxy§f§l)`);
        enterCommand();
        createBot();
    }
}

sendBot();
