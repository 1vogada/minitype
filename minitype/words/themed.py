"""Built-in themed word lists, available offline."""

from .builtin import BUILTIN

PROGRAMMING = """function variable class object array string integer boolean float
loop return import export const async await promise callback compile debug
deploy commit merge branch repository server client request response query
database schema index cache buffer stack queue heap pointer thread process
kernel runtime syntax parser token lambda closure iterator generator module
package library framework interface method property constructor instance
inherit override exception error null undefined true false lint test assert
mock refactor endpoint payload json yaml regex script terminal console shell
docker cloud http socket binary bitwise hash encrypt decode encode render
component state props hook event listener handler router middleware config
argument parameter default static public private protected abstract virtual
template generic typedef struct enum union tuple dictionary list set map
filter reduce sort search insert delete update select join commit rollback
transaction migration container cluster pipeline build release version patch
tag fork clone pull push fetch rebase stash diff log blame bisect cherry pick
recursion algorithm complexity memory garbage collector allocate free mutex
semaphore deadlock race condition scheduler interrupt register opcode compiler
interpreter bytecode assembly linker loader header source binary executable
""".split()

LEFT_HAND = """were state great after few feet tree street west wear award career
create decade exact extra faster garage grade sweater water beast bread craft
debt defeat degree desert draft dresser effect target access average brave cast
cave crew deaf dread fear fact fade fast fate fees gate gave gear grass raft
rare rate read rest sad safe sage save saw scar sea seat see set sweet tea tax
test text vase vast verb wade wage war was waste wax we wet zebra base bat bed
beer best bet cab car care cart case cat dad date deer dew ear east eat egg era
eve extract refresh retreat starve stared treat waters weave crate react
regard reverse secret severe swear tested vested wasted aware breed cedar
""".split()

RIGHT_HAND = """you him hip hill hop hook hum hunk ill ink inn ion jolly join joy junk
kill kin kiln kimono lily link lion lip loin lollipop look loop lump mill milk
mink moon mop mum nil nip noon nook nun oil onion only opinion oink pin pink
pill plum plump poll polo pool pop pulp pump punk puppy union unhook uphill
yolk yummy hymn holly hull homily monopoly million minimum mommy nylon pumpkin
ninja limp loony hoop kiosk moonlit lumpy ploy plunk """.split()

HOME_ROW = """add ads alas all ask asks dad dads fad fads fall falls flag flags flask
gag gal gall gas glad glass hall half has hash jag lad lads lag lash lass sad
saga sag salad salsa sash shall flash dash gash hag haggard flak gasks alfalfa
shag slag slash ash dahl""".split()


def _only(letters):
    return [w for w in BUILTIN if set(w) <= set(letters)]


def left_hand():
    return sorted(set(LEFT_HAND + _only("qwertasdfgzxcvb")))


def right_hand():
    return sorted(set(RIGHT_HAND + _only("yuiophjklnm")))


def home_row():
    return sorted(set(HOME_ROW + _only("asdfghjkl")))


THEMED = {
    "programming": lambda: list(dict.fromkeys(PROGRAMMING)),
    "left hand": left_hand,
    "right hand": right_hand,
    "home row": home_row,
}
