_himalaya() {
    local i cur prev opts cmd
    COMPREPLY=()
    if [[ "${BASH_VERSINFO[0]}" -ge 4 ]]; then
        cur="$2"
    else
        cur="${COMP_WORDS[COMP_CWORD]}"
    fi
    prev="$3"
    cmd=""
    opts=""

    for i in "${COMP_WORDS[@]:0:COMP_CWORD}"
    do
        case "${cmd},${i}" in
            ",$1")
                cmd="himalaya"
                ;;
            himalaya,account)
                cmd="himalaya__subcmd__account"
                ;;
            himalaya,attachment)
                cmd="himalaya__subcmd__attachment"
                ;;
            himalaya,completion)
                cmd="himalaya__subcmd__completion"
                ;;
            himalaya,envelope)
                cmd="himalaya__subcmd__envelope"
                ;;
            himalaya,flag)
                cmd="himalaya__subcmd__flag"
                ;;
            himalaya,gmail)
                cmd="himalaya__subcmd__gmail"
                ;;
            himalaya,help)
                cmd="himalaya__subcmd__help"
                ;;
            himalaya,imap)
                cmd="himalaya__subcmd__imap"
                ;;
            himalaya,jmap)
                cmd="himalaya__subcmd__jmap"
                ;;
            himalaya,json-schema)
                cmd="himalaya__subcmd__json__subcmd__schema"
                ;;
            himalaya,m2dir)
                cmd="himalaya__subcmd__m2dir"
                ;;
            himalaya,mailbox)
                cmd="himalaya__subcmd__mailbox"
                ;;
            himalaya,manual)
                cmd="himalaya__subcmd__manual"
                ;;
            himalaya,mbox)
                cmd="himalaya__subcmd__mailbox"
                ;;
            himalaya,message)
                cmd="himalaya__subcmd__message"
                ;;
            himalaya,msg)
                cmd="himalaya__subcmd__message"
                ;;
            himalaya,msgraph)
                cmd="himalaya__subcmd__msgraph"
                ;;
            himalaya,smtp)
                cmd="himalaya__subcmd__smtp"
                ;;
            himalaya__subcmd__account,check)
                cmd="himalaya__subcmd__account__subcmd__check"
                ;;
            himalaya__subcmd__account,help)
                cmd="himalaya__subcmd__account__subcmd__help"
                ;;
            himalaya__subcmd__account,list)
                cmd="himalaya__subcmd__account__subcmd__list"
                ;;
            himalaya__subcmd__account,ls)
                cmd="himalaya__subcmd__account__subcmd__list"
                ;;
            himalaya__subcmd__account__subcmd__help,check)
                cmd="himalaya__subcmd__account__subcmd__help__subcmd__check"
                ;;
            himalaya__subcmd__account__subcmd__help,help)
                cmd="himalaya__subcmd__account__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__account__subcmd__help,list)
                cmd="himalaya__subcmd__account__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__attachment,dl)
                cmd="himalaya__subcmd__attachment__subcmd__download"
                ;;
            himalaya__subcmd__attachment,download)
                cmd="himalaya__subcmd__attachment__subcmd__download"
                ;;
            himalaya__subcmd__attachment,help)
                cmd="himalaya__subcmd__attachment__subcmd__help"
                ;;
            himalaya__subcmd__attachment,list)
                cmd="himalaya__subcmd__attachment__subcmd__list"
                ;;
            himalaya__subcmd__attachment,ls)
                cmd="himalaya__subcmd__attachment__subcmd__list"
                ;;
            himalaya__subcmd__attachment__subcmd__help,download)
                cmd="himalaya__subcmd__attachment__subcmd__help__subcmd__download"
                ;;
            himalaya__subcmd__attachment__subcmd__help,help)
                cmd="himalaya__subcmd__attachment__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__attachment__subcmd__help,list)
                cmd="himalaya__subcmd__attachment__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__envelope,help)
                cmd="himalaya__subcmd__envelope__subcmd__help"
                ;;
            himalaya__subcmd__envelope,list)
                cmd="himalaya__subcmd__envelope__subcmd__list"
                ;;
            himalaya__subcmd__envelope,ls)
                cmd="himalaya__subcmd__envelope__subcmd__list"
                ;;
            himalaya__subcmd__envelope,search)
                cmd="himalaya__subcmd__envelope__subcmd__search"
                ;;
            himalaya__subcmd__envelope,sr)
                cmd="himalaya__subcmd__envelope__subcmd__search"
                ;;
            himalaya__subcmd__envelope__subcmd__help,help)
                cmd="himalaya__subcmd__envelope__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__envelope__subcmd__help,list)
                cmd="himalaya__subcmd__envelope__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__envelope__subcmd__help,search)
                cmd="himalaya__subcmd__envelope__subcmd__help__subcmd__search"
                ;;
            himalaya__subcmd__flag,add)
                cmd="himalaya__subcmd__flag__subcmd__add"
                ;;
            himalaya__subcmd__flag,help)
                cmd="himalaya__subcmd__flag__subcmd__help"
                ;;
            himalaya__subcmd__flag,remove)
                cmd="himalaya__subcmd__flag__subcmd__remove"
                ;;
            himalaya__subcmd__flag,rm)
                cmd="himalaya__subcmd__flag__subcmd__remove"
                ;;
            himalaya__subcmd__flag,set)
                cmd="himalaya__subcmd__flag__subcmd__set"
                ;;
            himalaya__subcmd__flag__subcmd__help,add)
                cmd="himalaya__subcmd__flag__subcmd__help__subcmd__add"
                ;;
            himalaya__subcmd__flag__subcmd__help,help)
                cmd="himalaya__subcmd__flag__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__flag__subcmd__help,remove)
                cmd="himalaya__subcmd__flag__subcmd__help__subcmd__remove"
                ;;
            himalaya__subcmd__flag__subcmd__help,set)
                cmd="himalaya__subcmd__flag__subcmd__help__subcmd__set"
                ;;
            himalaya__subcmd__gmail,attachment)
                cmd="himalaya__subcmd__gmail__subcmd__attachments"
                ;;
            himalaya__subcmd__gmail,attachments)
                cmd="himalaya__subcmd__gmail__subcmd__attachments"
                ;;
            himalaya__subcmd__gmail,draft)
                cmd="himalaya__subcmd__gmail__subcmd__drafts"
                ;;
            himalaya__subcmd__gmail,drafts)
                cmd="himalaya__subcmd__gmail__subcmd__drafts"
                ;;
            himalaya__subcmd__gmail,help)
                cmd="himalaya__subcmd__gmail__subcmd__help"
                ;;
            himalaya__subcmd__gmail,history)
                cmd="himalaya__subcmd__gmail__subcmd__history"
                ;;
            himalaya__subcmd__gmail,label)
                cmd="himalaya__subcmd__gmail__subcmd__labels"
                ;;
            himalaya__subcmd__gmail,labels)
                cmd="himalaya__subcmd__gmail__subcmd__labels"
                ;;
            himalaya__subcmd__gmail,message)
                cmd="himalaya__subcmd__gmail__subcmd__messages"
                ;;
            himalaya__subcmd__gmail,messages)
                cmd="himalaya__subcmd__gmail__subcmd__messages"
                ;;
            himalaya__subcmd__gmail,msg)
                cmd="himalaya__subcmd__gmail__subcmd__messages"
                ;;
            himalaya__subcmd__gmail,profile)
                cmd="himalaya__subcmd__gmail__subcmd__profile"
                ;;
            himalaya__subcmd__gmail,setting)
                cmd="himalaya__subcmd__gmail__subcmd__settings"
                ;;
            himalaya__subcmd__gmail,settings)
                cmd="himalaya__subcmd__gmail__subcmd__settings"
                ;;
            himalaya__subcmd__gmail,thread)
                cmd="himalaya__subcmd__gmail__subcmd__threads"
                ;;
            himalaya__subcmd__gmail,threads)
                cmd="himalaya__subcmd__gmail__subcmd__threads"
                ;;
            himalaya__subcmd__gmail__subcmd__attachments,get)
                cmd="himalaya__subcmd__gmail__subcmd__attachments__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__attachments,help)
                cmd="himalaya__subcmd__gmail__subcmd__attachments__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__attachments__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__attachments__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__attachments__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__attachments__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,create)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,del)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,delete)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,get)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,help)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,list)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,remove)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,rm)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,send)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__send"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts,update)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts__subcmd__help,create)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts__subcmd__help,delete)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts__subcmd__help,list)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts__subcmd__help,send)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__send"
                ;;
            himalaya__subcmd__gmail__subcmd__drafts__subcmd__help,update)
                cmd="himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__help,attachments)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__attachments"
                ;;
            himalaya__subcmd__gmail__subcmd__help,drafts)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__drafts"
                ;;
            himalaya__subcmd__gmail__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__help,history)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__history"
                ;;
            himalaya__subcmd__gmail__subcmd__help,labels)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__labels"
                ;;
            himalaya__subcmd__gmail__subcmd__help,messages)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages"
                ;;
            himalaya__subcmd__gmail__subcmd__help,profile)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__profile"
                ;;
            himalaya__subcmd__gmail__subcmd__help,settings)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings"
                ;;
            himalaya__subcmd__gmail__subcmd__help,threads)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__threads"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__attachments,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__attachments__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__drafts,create)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__drafts,delete)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__drafts,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__drafts,list)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__drafts,send)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__send"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__drafts,update)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__history,list)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__history__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__labels,create)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__labels,delete)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__labels,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__labels,list)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__labels,update)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,batch-delete)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__batch__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,batch-modify)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__batch__subcmd__modify"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,delete)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,import)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__import"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,insert)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__insert"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,list)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,modify)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__modify"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,send)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__send"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,trash)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__trash"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__messages,untrash)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__untrash"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__profile,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__profile__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings,auto-forwarding)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__auto__subcmd__forwarding"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings,delegates)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings,filters)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings,forwarding-addresses)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings,imap)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__imap"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings,language)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__language"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings,pop)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__pop"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings,send-as)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings,vacation)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__vacation"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__auto__subcmd__forwarding,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__auto__subcmd__forwarding,set)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates,create)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates,delete)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates,list)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters,create)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters,delete)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters,list)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses,create)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses,delete)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses,list)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__imap,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__imap__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__imap,set)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__imap__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__language,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__language__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__language,set)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__language__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__pop,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__pop__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__pop,set)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__pop__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as,create)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as,delete)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as,list)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as,update)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as,verify)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__verify"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__vacation,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__vacation__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__vacation,set)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__vacation__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__threads,delete)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__threads,get)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__threads,list)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__threads,modify)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__modify"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__threads,trash)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__trash"
                ;;
            himalaya__subcmd__gmail__subcmd__help__subcmd__threads,untrash)
                cmd="himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__untrash"
                ;;
            himalaya__subcmd__gmail__subcmd__history,help)
                cmd="himalaya__subcmd__gmail__subcmd__history__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__history,list)
                cmd="himalaya__subcmd__gmail__subcmd__history__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__history__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__history__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__history__subcmd__help,list)
                cmd="himalaya__subcmd__gmail__subcmd__history__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__labels,create)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__labels,del)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__labels,delete)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__labels,get)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__labels,help)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__labels,list)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__labels,remove)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__labels,rm)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__labels,update)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__labels__subcmd__help,create)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__labels__subcmd__help,delete)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__labels__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__labels__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__labels__subcmd__help,list)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__labels__subcmd__help,update)
                cmd="himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,batch-delete)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__batch__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,batch-modify)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__batch__subcmd__modify"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,del)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,delete)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,get)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,help)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,import)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__import"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,insert)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__insert"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,list)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,modify)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__modify"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,remove)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,rm)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,send)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__send"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,trash)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__trash"
                ;;
            himalaya__subcmd__gmail__subcmd__messages,untrash)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__untrash"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,batch-delete)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__batch__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,batch-modify)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__batch__subcmd__modify"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,delete)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,import)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__import"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,insert)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__insert"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,list)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,modify)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__modify"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,send)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__send"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,trash)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__trash"
                ;;
            himalaya__subcmd__gmail__subcmd__messages__subcmd__help,untrash)
                cmd="himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__untrash"
                ;;
            himalaya__subcmd__gmail__subcmd__profile,get)
                cmd="himalaya__subcmd__gmail__subcmd__profile__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__profile,help)
                cmd="himalaya__subcmd__gmail__subcmd__profile__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__profile__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__profile__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__profile__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__profile__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,auto-forwarding)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,autoforwarding)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,delegate)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,delegates)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,filter)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,filters)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,forwarding-address)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,forwarding-addresses)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,imap)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__imap"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,language)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__language"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,pop)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__pop"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,send-as)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,sendas)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as"
                ;;
            himalaya__subcmd__gmail__subcmd__settings,vacation)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding,update)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates,del)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates,remove)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates,rm)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters,del)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters,remove)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters,rm)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,del)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,remove)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,rm)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,auto-forwarding)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__auto__subcmd__forwarding"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,delegates)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,filters)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,forwarding-addresses)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,imap)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__imap"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,language)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__language"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,pop)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__pop"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,send-as)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help,vacation)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__vacation"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__auto__subcmd__forwarding,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__auto__subcmd__forwarding__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__auto__subcmd__forwarding,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__auto__subcmd__forwarding__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__imap,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__imap__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__imap,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__imap__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__language,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__language__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__language,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__language__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__pop,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__pop__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__pop,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__pop__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as,update)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as,verify)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__verify"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__vacation,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__vacation__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__vacation,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__vacation__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__imap,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__imap,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__imap,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__imap,update)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__language,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__language,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__language,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__language,update)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__pop,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__pop,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__pop,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__pop,update)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,del)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,remove)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,rm)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,update)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,verify)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__verify"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help,create)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help,delete)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help,list)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help,update)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__update"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help,verify)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__verify"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation,update)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help,set)
                cmd="himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help__subcmd__set"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,del)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,delete)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,get)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,help)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,list)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,modify)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__modify"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,remove)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,rm)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,trash)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__trash"
                ;;
            himalaya__subcmd__gmail__subcmd__threads,untrash)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__untrash"
                ;;
            himalaya__subcmd__gmail__subcmd__threads__subcmd__help,delete)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__gmail__subcmd__threads__subcmd__help,get)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__gmail__subcmd__threads__subcmd__help,help)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__gmail__subcmd__threads__subcmd__help,list)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__gmail__subcmd__threads__subcmd__help,modify)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__modify"
                ;;
            himalaya__subcmd__gmail__subcmd__threads__subcmd__help,trash)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__trash"
                ;;
            himalaya__subcmd__gmail__subcmd__threads__subcmd__help,untrash)
                cmd="himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__untrash"
                ;;
            himalaya__subcmd__help,account)
                cmd="himalaya__subcmd__help__subcmd__account"
                ;;
            himalaya__subcmd__help,attachment)
                cmd="himalaya__subcmd__help__subcmd__attachment"
                ;;
            himalaya__subcmd__help,completion)
                cmd="himalaya__subcmd__help__subcmd__completion"
                ;;
            himalaya__subcmd__help,envelope)
                cmd="himalaya__subcmd__help__subcmd__envelope"
                ;;
            himalaya__subcmd__help,flag)
                cmd="himalaya__subcmd__help__subcmd__flag"
                ;;
            himalaya__subcmd__help,gmail)
                cmd="himalaya__subcmd__help__subcmd__gmail"
                ;;
            himalaya__subcmd__help,help)
                cmd="himalaya__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__help,imap)
                cmd="himalaya__subcmd__help__subcmd__imap"
                ;;
            himalaya__subcmd__help,jmap)
                cmd="himalaya__subcmd__help__subcmd__jmap"
                ;;
            himalaya__subcmd__help,json-schema)
                cmd="himalaya__subcmd__help__subcmd__json__subcmd__schema"
                ;;
            himalaya__subcmd__help,m2dir)
                cmd="himalaya__subcmd__help__subcmd__m2dir"
                ;;
            himalaya__subcmd__help,mailbox)
                cmd="himalaya__subcmd__help__subcmd__mailbox"
                ;;
            himalaya__subcmd__help,manual)
                cmd="himalaya__subcmd__help__subcmd__manual"
                ;;
            himalaya__subcmd__help,message)
                cmd="himalaya__subcmd__help__subcmd__message"
                ;;
            himalaya__subcmd__help,msgraph)
                cmd="himalaya__subcmd__help__subcmd__msgraph"
                ;;
            himalaya__subcmd__help,smtp)
                cmd="himalaya__subcmd__help__subcmd__smtp"
                ;;
            himalaya__subcmd__help__subcmd__account,check)
                cmd="himalaya__subcmd__help__subcmd__account__subcmd__check"
                ;;
            himalaya__subcmd__help__subcmd__account,list)
                cmd="himalaya__subcmd__help__subcmd__account__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__attachment,download)
                cmd="himalaya__subcmd__help__subcmd__attachment__subcmd__download"
                ;;
            himalaya__subcmd__help__subcmd__attachment,list)
                cmd="himalaya__subcmd__help__subcmd__attachment__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__envelope,list)
                cmd="himalaya__subcmd__help__subcmd__envelope__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__envelope,search)
                cmd="himalaya__subcmd__help__subcmd__envelope__subcmd__search"
                ;;
            himalaya__subcmd__help__subcmd__flag,add)
                cmd="himalaya__subcmd__help__subcmd__flag__subcmd__add"
                ;;
            himalaya__subcmd__help__subcmd__flag,remove)
                cmd="himalaya__subcmd__help__subcmd__flag__subcmd__remove"
                ;;
            himalaya__subcmd__help__subcmd__flag,set)
                cmd="himalaya__subcmd__help__subcmd__flag__subcmd__set"
                ;;
            himalaya__subcmd__help__subcmd__gmail,attachments)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__attachments"
                ;;
            himalaya__subcmd__help__subcmd__gmail,drafts)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__drafts"
                ;;
            himalaya__subcmd__help__subcmd__gmail,history)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__history"
                ;;
            himalaya__subcmd__help__subcmd__gmail,labels)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__labels"
                ;;
            himalaya__subcmd__help__subcmd__gmail,messages)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages"
                ;;
            himalaya__subcmd__help__subcmd__gmail,profile)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__profile"
                ;;
            himalaya__subcmd__help__subcmd__gmail,settings)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings"
                ;;
            himalaya__subcmd__help__subcmd__gmail,threads)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__threads"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__attachments,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__attachments__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__drafts,create)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__drafts,delete)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__drafts,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__drafts,list)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__drafts,send)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__send"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__drafts,update)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__update"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__history,list)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__history__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__labels,create)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__labels,delete)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__labels,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__labels,list)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__labels,update)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__update"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,batch-delete)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__batch__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,batch-modify)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__batch__subcmd__modify"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,delete)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,import)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__import"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,insert)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__insert"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,list)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,modify)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__modify"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,send)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__send"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,trash)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__trash"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__messages,untrash)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__untrash"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__profile,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__profile__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings,auto-forwarding)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings,delegates)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings,filters)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings,forwarding-addresses)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings,imap)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__imap"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings,language)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__language"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings,pop)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__pop"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings,send-as)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings,vacation)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__vacation"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding,set)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__set"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates,create)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates,delete)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates,list)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters,create)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters,delete)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters,list)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,create)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,delete)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses,list)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__imap,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__imap,set)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__set"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__language,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__language,set)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__set"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__pop,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__pop,set)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__set"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,create)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,delete)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,list)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,update)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__update"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as,verify)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__verify"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__vacation,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__vacation,set)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__set"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__threads,delete)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__threads,get)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__threads,list)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__threads,modify)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__modify"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__threads,trash)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__trash"
                ;;
            himalaya__subcmd__help__subcmd__gmail__subcmd__threads,untrash)
                cmd="himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__untrash"
                ;;
            himalaya__subcmd__help__subcmd__imap,append)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__append"
                ;;
            himalaya__subcmd__help__subcmd__imap,close)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__close"
                ;;
            himalaya__subcmd__help__subcmd__imap,copy)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__copy"
                ;;
            himalaya__subcmd__help__subcmd__imap,create)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__imap,delete)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__imap,expunge)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__expunge"
                ;;
            himalaya__subcmd__help__subcmd__imap,fetch)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__fetch"
                ;;
            himalaya__subcmd__help__subcmd__imap,flags)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__flags"
                ;;
            himalaya__subcmd__help__subcmd__imap,id)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__id"
                ;;
            himalaya__subcmd__help__subcmd__imap,list)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__imap,move)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__move"
                ;;
            himalaya__subcmd__help__subcmd__imap,raw)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__raw"
                ;;
            himalaya__subcmd__help__subcmd__imap,rename)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__rename"
                ;;
            himalaya__subcmd__help__subcmd__imap,search)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__search"
                ;;
            himalaya__subcmd__help__subcmd__imap,select)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__select"
                ;;
            himalaya__subcmd__help__subcmd__imap,sort)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__sort"
                ;;
            himalaya__subcmd__help__subcmd__imap,status)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__status"
                ;;
            himalaya__subcmd__help__subcmd__imap,store)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__store"
                ;;
            himalaya__subcmd__help__subcmd__imap,subscribe)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__subscribe"
                ;;
            himalaya__subcmd__help__subcmd__imap,thread)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__thread"
                ;;
            himalaya__subcmd__help__subcmd__imap,unselect)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__unselect"
                ;;
            himalaya__subcmd__help__subcmd__imap,unsubscribe)
                cmd="himalaya__subcmd__help__subcmd__imap__subcmd__unsubscribe"
                ;;
            himalaya__subcmd__help__subcmd__jmap,email)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email"
                ;;
            himalaya__subcmd__help__subcmd__jmap,identity)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__identity"
                ;;
            himalaya__subcmd__help__subcmd__jmap,mailbox)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox"
                ;;
            himalaya__subcmd__help__subcmd__jmap,query)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__query"
                ;;
            himalaya__subcmd__help__subcmd__jmap,submission)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__submission"
                ;;
            himalaya__subcmd__help__subcmd__jmap,thread)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__thread"
                ;;
            himalaya__subcmd__help__subcmd__jmap,vacation-response)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__vacation__subcmd__response"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__email,copy)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__copy"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__email,delete)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__email,export)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__export"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__email,get)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__email,import)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__import"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__email,parse)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__parse"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__email,query)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__query"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__email,read)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__read"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__email,update)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__update"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__identity,create)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__identity__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__identity,delete)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__identity__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__identity,get)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__identity__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__identity,update)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__identity__subcmd__update"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox,create)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox,destroy)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__destroy"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox,get)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox,query)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__query"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox,update)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__update"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__submission,cancel)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__submission__subcmd__cancel"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__submission,create)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__submission__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__submission,get)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__submission__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__submission,query)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__submission__subcmd__query"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__thread,get)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__thread__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__vacation__subcmd__response,get)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__jmap__subcmd__vacation__subcmd__response,set)
                cmd="himalaya__subcmd__help__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__set"
                ;;
            himalaya__subcmd__help__subcmd__m2dir,create)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__m2dir,delete)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__m2dir,flags)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__flags"
                ;;
            himalaya__subcmd__help__subcmd__m2dir,list)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__m2dir,messages)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__messages"
                ;;
            himalaya__subcmd__help__subcmd__m2dir__subcmd__flags,add)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__flags__subcmd__add"
                ;;
            himalaya__subcmd__help__subcmd__m2dir__subcmd__flags,list)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__flags__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__m2dir__subcmd__flags,remove)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__flags__subcmd__remove"
                ;;
            himalaya__subcmd__help__subcmd__m2dir__subcmd__flags,set)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__flags__subcmd__set"
                ;;
            himalaya__subcmd__help__subcmd__m2dir__subcmd__messages,save)
                cmd="himalaya__subcmd__help__subcmd__m2dir__subcmd__messages__subcmd__save"
                ;;
            himalaya__subcmd__help__subcmd__mailbox,list)
                cmd="himalaya__subcmd__help__subcmd__mailbox__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__message,add)
                cmd="himalaya__subcmd__help__subcmd__message__subcmd__add"
                ;;
            himalaya__subcmd__help__subcmd__message,compose)
                cmd="himalaya__subcmd__help__subcmd__message__subcmd__compose"
                ;;
            himalaya__subcmd__help__subcmd__message,copy)
                cmd="himalaya__subcmd__help__subcmd__message__subcmd__copy"
                ;;
            himalaya__subcmd__help__subcmd__message,forward)
                cmd="himalaya__subcmd__help__subcmd__message__subcmd__forward"
                ;;
            himalaya__subcmd__help__subcmd__message,move)
                cmd="himalaya__subcmd__help__subcmd__message__subcmd__move"
                ;;
            himalaya__subcmd__help__subcmd__message,read)
                cmd="himalaya__subcmd__help__subcmd__message__subcmd__read"
                ;;
            himalaya__subcmd__help__subcmd__message,reply)
                cmd="himalaya__subcmd__help__subcmd__message__subcmd__reply"
                ;;
            himalaya__subcmd__help__subcmd__message,send)
                cmd="himalaya__subcmd__help__subcmd__message__subcmd__send"
                ;;
            himalaya__subcmd__help__subcmd__msgraph,attachment)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment"
                ;;
            himalaya__subcmd__help__subcmd__msgraph,mail-folder)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder"
                ;;
            himalaya__subcmd__help__subcmd__msgraph,message)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__message"
                ;;
            himalaya__subcmd__help__subcmd__msgraph,profile)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__profile"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment,create)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment,delete)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment,get)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment,list)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder,child-folders)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__child__subcmd__folders"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder,copy)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__copy"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder,create)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder,delete)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder,get)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder,list)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder,move)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__move"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder,rename)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__rename"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__message,copy)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__copy"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__message,create)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__create"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__message,delete)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__delete"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__message,get)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__message,list)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__list"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__message,move)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__move"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__message,send)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__send"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__message,update)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__update"
                ;;
            himalaya__subcmd__help__subcmd__msgraph__subcmd__profile,get)
                cmd="himalaya__subcmd__help__subcmd__msgraph__subcmd__profile__subcmd__get"
                ;;
            himalaya__subcmd__help__subcmd__smtp,raw)
                cmd="himalaya__subcmd__help__subcmd__smtp__subcmd__raw"
                ;;
            himalaya__subcmd__help__subcmd__smtp,send)
                cmd="himalaya__subcmd__help__subcmd__smtp__subcmd__send"
                ;;
            himalaya__subcmd__imap,append)
                cmd="himalaya__subcmd__imap__subcmd__append"
                ;;
            himalaya__subcmd__imap,close)
                cmd="himalaya__subcmd__imap__subcmd__close"
                ;;
            himalaya__subcmd__imap,copy)
                cmd="himalaya__subcmd__imap__subcmd__copy"
                ;;
            himalaya__subcmd__imap,create)
                cmd="himalaya__subcmd__imap__subcmd__create"
                ;;
            himalaya__subcmd__imap,delete)
                cmd="himalaya__subcmd__imap__subcmd__delete"
                ;;
            himalaya__subcmd__imap,expunge)
                cmd="himalaya__subcmd__imap__subcmd__expunge"
                ;;
            himalaya__subcmd__imap,fetch)
                cmd="himalaya__subcmd__imap__subcmd__fetch"
                ;;
            himalaya__subcmd__imap,flags)
                cmd="himalaya__subcmd__imap__subcmd__flags"
                ;;
            himalaya__subcmd__imap,help)
                cmd="himalaya__subcmd__imap__subcmd__help"
                ;;
            himalaya__subcmd__imap,id)
                cmd="himalaya__subcmd__imap__subcmd__id"
                ;;
            himalaya__subcmd__imap,list)
                cmd="himalaya__subcmd__imap__subcmd__list"
                ;;
            himalaya__subcmd__imap,move)
                cmd="himalaya__subcmd__imap__subcmd__move"
                ;;
            himalaya__subcmd__imap,raw)
                cmd="himalaya__subcmd__imap__subcmd__raw"
                ;;
            himalaya__subcmd__imap,rename)
                cmd="himalaya__subcmd__imap__subcmd__rename"
                ;;
            himalaya__subcmd__imap,search)
                cmd="himalaya__subcmd__imap__subcmd__search"
                ;;
            himalaya__subcmd__imap,select)
                cmd="himalaya__subcmd__imap__subcmd__select"
                ;;
            himalaya__subcmd__imap,sort)
                cmd="himalaya__subcmd__imap__subcmd__sort"
                ;;
            himalaya__subcmd__imap,status)
                cmd="himalaya__subcmd__imap__subcmd__status"
                ;;
            himalaya__subcmd__imap,store)
                cmd="himalaya__subcmd__imap__subcmd__store"
                ;;
            himalaya__subcmd__imap,subscribe)
                cmd="himalaya__subcmd__imap__subcmd__subscribe"
                ;;
            himalaya__subcmd__imap,thread)
                cmd="himalaya__subcmd__imap__subcmd__thread"
                ;;
            himalaya__subcmd__imap,unselect)
                cmd="himalaya__subcmd__imap__subcmd__unselect"
                ;;
            himalaya__subcmd__imap,unsubscribe)
                cmd="himalaya__subcmd__imap__subcmd__unsubscribe"
                ;;
            himalaya__subcmd__imap__subcmd__help,append)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__append"
                ;;
            himalaya__subcmd__imap__subcmd__help,close)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__close"
                ;;
            himalaya__subcmd__imap__subcmd__help,copy)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__copy"
                ;;
            himalaya__subcmd__imap__subcmd__help,create)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__imap__subcmd__help,delete)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__imap__subcmd__help,expunge)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__expunge"
                ;;
            himalaya__subcmd__imap__subcmd__help,fetch)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__fetch"
                ;;
            himalaya__subcmd__imap__subcmd__help,flags)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__flags"
                ;;
            himalaya__subcmd__imap__subcmd__help,help)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__imap__subcmd__help,id)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__id"
                ;;
            himalaya__subcmd__imap__subcmd__help,list)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__imap__subcmd__help,move)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__move"
                ;;
            himalaya__subcmd__imap__subcmd__help,raw)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__raw"
                ;;
            himalaya__subcmd__imap__subcmd__help,rename)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__rename"
                ;;
            himalaya__subcmd__imap__subcmd__help,search)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__search"
                ;;
            himalaya__subcmd__imap__subcmd__help,select)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__select"
                ;;
            himalaya__subcmd__imap__subcmd__help,sort)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__sort"
                ;;
            himalaya__subcmd__imap__subcmd__help,status)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__status"
                ;;
            himalaya__subcmd__imap__subcmd__help,store)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__store"
                ;;
            himalaya__subcmd__imap__subcmd__help,subscribe)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__subscribe"
                ;;
            himalaya__subcmd__imap__subcmd__help,thread)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__thread"
                ;;
            himalaya__subcmd__imap__subcmd__help,unselect)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__unselect"
                ;;
            himalaya__subcmd__imap__subcmd__help,unsubscribe)
                cmd="himalaya__subcmd__imap__subcmd__help__subcmd__unsubscribe"
                ;;
            himalaya__subcmd__jmap,email)
                cmd="himalaya__subcmd__jmap__subcmd__email"
                ;;
            himalaya__subcmd__jmap,help)
                cmd="himalaya__subcmd__jmap__subcmd__help"
                ;;
            himalaya__subcmd__jmap,identity)
                cmd="himalaya__subcmd__jmap__subcmd__identity"
                ;;
            himalaya__subcmd__jmap,mailbox)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox"
                ;;
            himalaya__subcmd__jmap,mbox)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox"
                ;;
            himalaya__subcmd__jmap,query)
                cmd="himalaya__subcmd__jmap__subcmd__query"
                ;;
            himalaya__subcmd__jmap,submission)
                cmd="himalaya__subcmd__jmap__subcmd__submission"
                ;;
            himalaya__subcmd__jmap,thread)
                cmd="himalaya__subcmd__jmap__subcmd__thread"
                ;;
            himalaya__subcmd__jmap,vacation)
                cmd="himalaya__subcmd__jmap__subcmd__vacation__subcmd__response"
                ;;
            himalaya__subcmd__jmap,vacation-response)
                cmd="himalaya__subcmd__jmap__subcmd__vacation__subcmd__response"
                ;;
            himalaya__subcmd__jmap__subcmd__email,copy)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__copy"
                ;;
            himalaya__subcmd__jmap__subcmd__email,delete)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__delete"
                ;;
            himalaya__subcmd__jmap__subcmd__email,export)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__export"
                ;;
            himalaya__subcmd__jmap__subcmd__email,get)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__email,help)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__email,import)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__import"
                ;;
            himalaya__subcmd__jmap__subcmd__email,parse)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__parse"
                ;;
            himalaya__subcmd__jmap__subcmd__email,query)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__email,read)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__read"
                ;;
            himalaya__subcmd__jmap__subcmd__email,update)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__update"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,copy)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__copy"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,delete)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,export)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__export"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,get)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,help)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,import)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__import"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,parse)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__parse"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,query)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,read)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__read"
                ;;
            himalaya__subcmd__jmap__subcmd__email__subcmd__help,update)
                cmd="himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__update"
                ;;
            himalaya__subcmd__jmap__subcmd__help,email)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email"
                ;;
            himalaya__subcmd__jmap__subcmd__help,help)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__help,identity)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__identity"
                ;;
            himalaya__subcmd__jmap__subcmd__help,mailbox)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox"
                ;;
            himalaya__subcmd__jmap__subcmd__help,query)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__help,submission)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__submission"
                ;;
            himalaya__subcmd__jmap__subcmd__help,thread)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__thread"
                ;;
            himalaya__subcmd__jmap__subcmd__help,vacation-response)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__vacation__subcmd__response"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__email,copy)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__copy"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__email,delete)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__delete"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__email,export)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__export"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__email,get)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__email,import)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__import"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__email,parse)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__parse"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__email,query)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__email,read)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__read"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__email,update)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__update"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__identity,create)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__identity__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__identity,delete)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__identity__subcmd__delete"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__identity,get)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__identity__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__identity,update)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__identity__subcmd__update"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox,create)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox,destroy)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__destroy"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox,get)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox,query)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox,update)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__update"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__submission,cancel)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__submission__subcmd__cancel"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__submission,create)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__submission__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__submission,get)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__submission__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__submission,query)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__submission__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__thread,get)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__thread__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__vacation__subcmd__response,get)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__vacation__subcmd__response__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__help__subcmd__vacation__subcmd__response,set)
                cmd="himalaya__subcmd__jmap__subcmd__help__subcmd__vacation__subcmd__response__subcmd__set"
                ;;
            himalaya__subcmd__jmap__subcmd__identity,create)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__identity,delete)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__delete"
                ;;
            himalaya__subcmd__jmap__subcmd__identity,get)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__identity,help)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__identity,update)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__update"
                ;;
            himalaya__subcmd__jmap__subcmd__identity__subcmd__help,create)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__identity__subcmd__help,delete)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__jmap__subcmd__identity__subcmd__help,get)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__identity__subcmd__help,help)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__identity__subcmd__help,update)
                cmd="himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__update"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,add)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,create)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,del)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__destroy"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,delete)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__destroy"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,destroy)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__destroy"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,get)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,help)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,new)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,query)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,remove)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__destroy"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,rm)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__destroy"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox,update)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__update"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help,create)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help,destroy)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__destroy"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help,get)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help,help)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help,query)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help,update)
                cmd="himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__update"
                ;;
            himalaya__subcmd__jmap__subcmd__submission,cancel)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__cancel"
                ;;
            himalaya__subcmd__jmap__subcmd__submission,create)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__submission,get)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__submission,help)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__submission,query)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__submission__subcmd__help,cancel)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__cancel"
                ;;
            himalaya__subcmd__jmap__subcmd__submission__subcmd__help,create)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__jmap__subcmd__submission__subcmd__help,get)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__submission__subcmd__help,help)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__submission__subcmd__help,query)
                cmd="himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__query"
                ;;
            himalaya__subcmd__jmap__subcmd__thread,get)
                cmd="himalaya__subcmd__jmap__subcmd__thread__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__thread,help)
                cmd="himalaya__subcmd__jmap__subcmd__thread__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__thread__subcmd__help,get)
                cmd="himalaya__subcmd__jmap__subcmd__thread__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__thread__subcmd__help,help)
                cmd="himalaya__subcmd__jmap__subcmd__thread__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__vacation__subcmd__response,get)
                cmd="himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__vacation__subcmd__response,help)
                cmd="himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__vacation__subcmd__response,set)
                cmd="himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__set"
                ;;
            himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help,get)
                cmd="himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help,help)
                cmd="himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help,set)
                cmd="himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help__subcmd__set"
                ;;
            himalaya__subcmd__m2dir,create)
                cmd="himalaya__subcmd__m2dir__subcmd__create"
                ;;
            himalaya__subcmd__m2dir,delete)
                cmd="himalaya__subcmd__m2dir__subcmd__delete"
                ;;
            himalaya__subcmd__m2dir,flags)
                cmd="himalaya__subcmd__m2dir__subcmd__flags"
                ;;
            himalaya__subcmd__m2dir,help)
                cmd="himalaya__subcmd__m2dir__subcmd__help"
                ;;
            himalaya__subcmd__m2dir,list)
                cmd="himalaya__subcmd__m2dir__subcmd__list"
                ;;
            himalaya__subcmd__m2dir,messages)
                cmd="himalaya__subcmd__m2dir__subcmd__messages"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags,add)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__add"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags,help)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__help"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags,list)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__list"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags,remove)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__remove"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags,set)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__set"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags__subcmd__help,add)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__add"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags__subcmd__help,help)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags__subcmd__help,list)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags__subcmd__help,remove)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__remove"
                ;;
            himalaya__subcmd__m2dir__subcmd__flags__subcmd__help,set)
                cmd="himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__set"
                ;;
            himalaya__subcmd__m2dir__subcmd__help,create)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__m2dir__subcmd__help,delete)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__m2dir__subcmd__help,flags)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__flags"
                ;;
            himalaya__subcmd__m2dir__subcmd__help,help)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__m2dir__subcmd__help,list)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__m2dir__subcmd__help,messages)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__messages"
                ;;
            himalaya__subcmd__m2dir__subcmd__help__subcmd__flags,add)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__flags__subcmd__add"
                ;;
            himalaya__subcmd__m2dir__subcmd__help__subcmd__flags,list)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__flags__subcmd__list"
                ;;
            himalaya__subcmd__m2dir__subcmd__help__subcmd__flags,remove)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__flags__subcmd__remove"
                ;;
            himalaya__subcmd__m2dir__subcmd__help__subcmd__flags,set)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__flags__subcmd__set"
                ;;
            himalaya__subcmd__m2dir__subcmd__help__subcmd__messages,save)
                cmd="himalaya__subcmd__m2dir__subcmd__help__subcmd__messages__subcmd__save"
                ;;
            himalaya__subcmd__m2dir__subcmd__messages,help)
                cmd="himalaya__subcmd__m2dir__subcmd__messages__subcmd__help"
                ;;
            himalaya__subcmd__m2dir__subcmd__messages,save)
                cmd="himalaya__subcmd__m2dir__subcmd__messages__subcmd__save"
                ;;
            himalaya__subcmd__m2dir__subcmd__messages__subcmd__help,help)
                cmd="himalaya__subcmd__m2dir__subcmd__messages__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__m2dir__subcmd__messages__subcmd__help,save)
                cmd="himalaya__subcmd__m2dir__subcmd__messages__subcmd__help__subcmd__save"
                ;;
            himalaya__subcmd__mailbox,help)
                cmd="himalaya__subcmd__mailbox__subcmd__help"
                ;;
            himalaya__subcmd__mailbox,list)
                cmd="himalaya__subcmd__mailbox__subcmd__list"
                ;;
            himalaya__subcmd__mailbox,ls)
                cmd="himalaya__subcmd__mailbox__subcmd__list"
                ;;
            himalaya__subcmd__mailbox__subcmd__help,help)
                cmd="himalaya__subcmd__mailbox__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__mailbox__subcmd__help,list)
                cmd="himalaya__subcmd__mailbox__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__message,add)
                cmd="himalaya__subcmd__message__subcmd__add"
                ;;
            himalaya__subcmd__message,compose)
                cmd="himalaya__subcmd__message__subcmd__compose"
                ;;
            himalaya__subcmd__message,copy)
                cmd="himalaya__subcmd__message__subcmd__copy"
                ;;
            himalaya__subcmd__message,cp)
                cmd="himalaya__subcmd__message__subcmd__copy"
                ;;
            himalaya__subcmd__message,forward)
                cmd="himalaya__subcmd__message__subcmd__forward"
                ;;
            himalaya__subcmd__message,fwd)
                cmd="himalaya__subcmd__message__subcmd__forward"
                ;;
            himalaya__subcmd__message,help)
                cmd="himalaya__subcmd__message__subcmd__help"
                ;;
            himalaya__subcmd__message,move)
                cmd="himalaya__subcmd__message__subcmd__move"
                ;;
            himalaya__subcmd__message,mv)
                cmd="himalaya__subcmd__message__subcmd__move"
                ;;
            himalaya__subcmd__message,read)
                cmd="himalaya__subcmd__message__subcmd__read"
                ;;
            himalaya__subcmd__message,reply)
                cmd="himalaya__subcmd__message__subcmd__reply"
                ;;
            himalaya__subcmd__message,save)
                cmd="himalaya__subcmd__message__subcmd__add"
                ;;
            himalaya__subcmd__message,send)
                cmd="himalaya__subcmd__message__subcmd__send"
                ;;
            himalaya__subcmd__message,write)
                cmd="himalaya__subcmd__message__subcmd__compose"
                ;;
            himalaya__subcmd__message__subcmd__help,add)
                cmd="himalaya__subcmd__message__subcmd__help__subcmd__add"
                ;;
            himalaya__subcmd__message__subcmd__help,compose)
                cmd="himalaya__subcmd__message__subcmd__help__subcmd__compose"
                ;;
            himalaya__subcmd__message__subcmd__help,copy)
                cmd="himalaya__subcmd__message__subcmd__help__subcmd__copy"
                ;;
            himalaya__subcmd__message__subcmd__help,forward)
                cmd="himalaya__subcmd__message__subcmd__help__subcmd__forward"
                ;;
            himalaya__subcmd__message__subcmd__help,help)
                cmd="himalaya__subcmd__message__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__message__subcmd__help,move)
                cmd="himalaya__subcmd__message__subcmd__help__subcmd__move"
                ;;
            himalaya__subcmd__message__subcmd__help,read)
                cmd="himalaya__subcmd__message__subcmd__help__subcmd__read"
                ;;
            himalaya__subcmd__message__subcmd__help,reply)
                cmd="himalaya__subcmd__message__subcmd__help__subcmd__reply"
                ;;
            himalaya__subcmd__message__subcmd__help,send)
                cmd="himalaya__subcmd__message__subcmd__help__subcmd__send"
                ;;
            himalaya__subcmd__msgraph,attachment)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment"
                ;;
            himalaya__subcmd__msgraph,attachments)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment"
                ;;
            himalaya__subcmd__msgraph,folder)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder"
                ;;
            himalaya__subcmd__msgraph,folders)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder"
                ;;
            himalaya__subcmd__msgraph,help)
                cmd="himalaya__subcmd__msgraph__subcmd__help"
                ;;
            himalaya__subcmd__msgraph,mail-folder)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder"
                ;;
            himalaya__subcmd__msgraph,mail-folders)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder"
                ;;
            himalaya__subcmd__msgraph,message)
                cmd="himalaya__subcmd__msgraph__subcmd__message"
                ;;
            himalaya__subcmd__msgraph,messages)
                cmd="himalaya__subcmd__msgraph__subcmd__message"
                ;;
            himalaya__subcmd__msgraph,msg)
                cmd="himalaya__subcmd__msgraph__subcmd__message"
                ;;
            himalaya__subcmd__msgraph,profile)
                cmd="himalaya__subcmd__msgraph__subcmd__profile"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment,create)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__create"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment,del)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment,delete)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment,get)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment,help)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment,list)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__list"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment,remove)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment,rm)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help,create)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help,delete)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help,get)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help,help)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help,list)
                cmd="himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__msgraph__subcmd__help,attachment)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment"
                ;;
            himalaya__subcmd__msgraph__subcmd__help,help)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__msgraph__subcmd__help,mail-folder)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder"
                ;;
            himalaya__subcmd__msgraph__subcmd__help,message)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__message"
                ;;
            himalaya__subcmd__msgraph__subcmd__help,profile)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__profile"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment,create)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment__subcmd__create"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment,delete)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment,get)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment,list)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment__subcmd__list"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder,child-folders)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__child__subcmd__folders"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder,copy)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__copy"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder,create)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__create"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder,delete)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder,get)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder,list)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__list"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder,move)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__move"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder,rename)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__rename"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__message,copy)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__copy"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__message,create)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__create"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__message,delete)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__message,get)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__message,list)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__list"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__message,move)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__move"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__message,send)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__send"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__message,update)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__update"
                ;;
            himalaya__subcmd__msgraph__subcmd__help__subcmd__profile,get)
                cmd="himalaya__subcmd__msgraph__subcmd__help__subcmd__profile__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,child)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__child__subcmd__folders"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,child-folders)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__child__subcmd__folders"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,children)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__child__subcmd__folders"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,copy)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__copy"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,create)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__create"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,del)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,delete)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,get)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,help)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,list)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__list"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,move)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__move"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,remove)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,rename)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__rename"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder,rm)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help,child-folders)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__child__subcmd__folders"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help,copy)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__copy"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help,create)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help,delete)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help,get)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help,help)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help,list)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help,move)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__move"
                ;;
            himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help,rename)
                cmd="himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__rename"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,copy)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__copy"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,create)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__create"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,del)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,delete)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,get)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,help)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,list)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__list"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,move)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__move"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,remove)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,rm)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,send)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__send"
                ;;
            himalaya__subcmd__msgraph__subcmd__message,update)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__update"
                ;;
            himalaya__subcmd__msgraph__subcmd__message__subcmd__help,copy)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__copy"
                ;;
            himalaya__subcmd__msgraph__subcmd__message__subcmd__help,create)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__create"
                ;;
            himalaya__subcmd__msgraph__subcmd__message__subcmd__help,delete)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__delete"
                ;;
            himalaya__subcmd__msgraph__subcmd__message__subcmd__help,get)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__message__subcmd__help,help)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__msgraph__subcmd__message__subcmd__help,list)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__list"
                ;;
            himalaya__subcmd__msgraph__subcmd__message__subcmd__help,move)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__move"
                ;;
            himalaya__subcmd__msgraph__subcmd__message__subcmd__help,send)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__send"
                ;;
            himalaya__subcmd__msgraph__subcmd__message__subcmd__help,update)
                cmd="himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__update"
                ;;
            himalaya__subcmd__msgraph__subcmd__profile,get)
                cmd="himalaya__subcmd__msgraph__subcmd__profile__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__profile,help)
                cmd="himalaya__subcmd__msgraph__subcmd__profile__subcmd__help"
                ;;
            himalaya__subcmd__msgraph__subcmd__profile__subcmd__help,get)
                cmd="himalaya__subcmd__msgraph__subcmd__profile__subcmd__help__subcmd__get"
                ;;
            himalaya__subcmd__msgraph__subcmd__profile__subcmd__help,help)
                cmd="himalaya__subcmd__msgraph__subcmd__profile__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__smtp,help)
                cmd="himalaya__subcmd__smtp__subcmd__help"
                ;;
            himalaya__subcmd__smtp,raw)
                cmd="himalaya__subcmd__smtp__subcmd__raw"
                ;;
            himalaya__subcmd__smtp,send)
                cmd="himalaya__subcmd__smtp__subcmd__send"
                ;;
            himalaya__subcmd__smtp__subcmd__help,help)
                cmd="himalaya__subcmd__smtp__subcmd__help__subcmd__help"
                ;;
            himalaya__subcmd__smtp__subcmd__help,raw)
                cmd="himalaya__subcmd__smtp__subcmd__help__subcmd__raw"
                ;;
            himalaya__subcmd__smtp__subcmd__help,send)
                cmd="himalaya__subcmd__smtp__subcmd__help__subcmd__send"
                ;;
            *)
                ;;
        esac
    done

    case "${cmd}" in
        himalaya)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version mailbox mbox envelope flag message msg attachment imap jmap gmail msgraph m2dir smtp account completion manual json-schema help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 1 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__account)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list ls check help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__account__subcmd__check)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__account__subcmd__help)
            opts="list check help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__account__subcmd__help__subcmd__check)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__account__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__account__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__account__subcmd__list)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__attachment)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list ls download dl help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__attachment__subcmd__download)
            opts="-m -d -c -a -b -h -V --mailbox --dir --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --dir)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -d)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__attachment__subcmd__help)
            opts="list download help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__attachment__subcmd__help__subcmd__download)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__attachment__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__attachment__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__attachment__subcmd__list)
            opts="-m -i -c -a -b -h -V --mailbox --inline --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__completion)
            opts="-d -c -a -b -h -V --dir --config --account --backend --json --log --log-level --log-file --help --version bash elvish fish powershell zsh"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --dir)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -d)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__envelope)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list ls search sr help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__envelope__subcmd__help)
            opts="list search help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__envelope__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__envelope__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__envelope__subcmd__help__subcmd__search)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__envelope__subcmd__list)
            opts="-m -p -s -w -r -c -a -b -h -V --mailbox --page --page-size --max-width --recipient --has-attachment --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -p)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page-size)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --max-width)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -w)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__envelope__subcmd__search)
            opts="-m -p -s -w -r -c -a -b -h -V --mailbox --page --page-size --max-width --recipient --has-attachment --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -p)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page-size)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --max-width)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -w)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__flag)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version add set remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__flag__subcmd__add)
            opts="-m -f -c -a -b -h -V --mailbox --flag --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --flag)
                    COMPREPLY=($(compgen -W "seen answered flagged draft" -- "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -W "seen answered flagged draft" -- "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__flag__subcmd__help)
            opts="add set remove help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__flag__subcmd__help__subcmd__add)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__flag__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__flag__subcmd__help__subcmd__remove)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__flag__subcmd__help__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__flag__subcmd__remove)
            opts="-m -f -c -a -b -h -V --mailbox --flag --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --flag)
                    COMPREPLY=($(compgen -W "seen answered flagged draft" -- "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -W "seen answered flagged draft" -- "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__flag__subcmd__set)
            opts="-m -f -c -a -b -h -V --mailbox --flag --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --flag)
                    COMPREPLY=($(compgen -W "seen answered flagged draft" -- "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -W "seen answered flagged draft" -- "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version profile labels label messages message msg attachments attachment drafts draft threads thread history settings setting help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__attachments)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__attachments__subcmd__get)
            opts="-o -c -a -b -h -V --output --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --output)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -o)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__attachments__subcmd__help)
            opts="get help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__attachments__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__attachments__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get create update send delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__create)
            opts="-c -a -b -h -V --thread-id --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --thread-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__get)
            opts="-c -a -b -h -V --format --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --format)
                    COMPREPLY=($(compgen -W "minimal full raw metadata" -- "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__help)
            opts="list get create update send delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__help__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__list)
            opts="-q -s -c -a -b -h -V --query --max-results --page-token --include-spam-trash --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --query)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -q)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --max-results)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page-token)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__send)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__drafts__subcmd__update)
            opts="-c -a -b -h -V --thread-id --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --thread-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help)
            opts="profile labels messages attachments drafts threads history settings help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__attachments)
            opts="get"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__attachments__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__drafts)
            opts="list get create update send delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__drafts__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__history)
            opts="list"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__history__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__labels)
            opts="list get create update delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__labels__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages)
            opts="list get send import insert modify trash untrash delete batch-modify batch-delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__batch__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__batch__subcmd__modify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__import)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__insert)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__modify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__trash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__messages__subcmd__untrash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__profile)
            opts="get"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__profile__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings)
            opts="vacation imap pop language auto-forwarding filters forwarding-addresses delegates send-as"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__auto__subcmd__forwarding)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__delegates__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__filters__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__imap)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__imap__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__imap__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__language)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__language__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__language__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__pop)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__pop__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__pop__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as)
            opts="list get create update delete verify"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__send__subcmd__as__subcmd__verify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__vacation)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__vacation__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__settings__subcmd__vacation__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__threads)
            opts="list get modify trash untrash delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__modify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__trash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__help__subcmd__threads__subcmd__untrash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__history)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__history__subcmd__help)
            opts="list help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__history__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__history__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__history__subcmd__list)
            opts="-s -c -a -b -h -V --start-history-id --label-id --history-type --max-results --page-token --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --start-history-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --label-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --history-type)
                    COMPREPLY=($(compgen -W "messageAdded messageDeleted labelAdded labelRemoved" -- "${cur}"))
                    return 0
                    ;;
                --max-results)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page-token)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get create update delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__create)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__help)
            opts="list get create update delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__help__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__list)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__labels__subcmd__update)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get send import insert modify trash untrash delete del remove rm batch-modify batch-delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__batch__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__batch__subcmd__modify)
            opts="-c -a -b -h -V --add-label --remove-label --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --add-label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --remove-label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__get)
            opts="-c -a -b -h -V --format --header --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --format)
                    COMPREPLY=($(compgen -W "minimal full raw metadata" -- "${cur}"))
                    return 0
                    ;;
                --header)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help)
            opts="list get send import insert modify trash untrash delete batch-modify batch-delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__batch__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__batch__subcmd__modify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__import)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__insert)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__modify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__trash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__help__subcmd__untrash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__import)
            opts="-c -a -b -h -V --label --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__insert)
            opts="-c -a -b -h -V --label --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__list)
            opts="-q -l -s -c -a -b -h -V --query --label --max-results --page-token --include-spam-trash --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --query)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -q)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -l)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --max-results)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page-token)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__modify)
            opts="-c -a -b -h -V --add-label --remove-label --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --add-label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --remove-label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__send)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__trash)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__messages__subcmd__untrash)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__profile)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__profile__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__profile__subcmd__help)
            opts="get help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__profile__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__profile__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version vacation imap pop language auto-forwarding autoforwarding filters filter forwarding-addresses forwarding-address delegates delegate send-as sendas help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get set update help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help)
            opts="get set help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__help__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__set)
            opts="-c -a -b -h -V --enable --disable --email-address --disposition --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --email-address)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --disposition)
                    COMPREPLY=($(compgen -W "leaveInInbox archive trash markRead" -- "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get create delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__create)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help)
            opts="list get create delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__list)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get create delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__create)
            opts="-c -a -b -h -V --from --to --subject --query --negated-query --has-attachment --add-label --remove-label --forward --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --query)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --negated-query)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --add-label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --remove-label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --forward)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help)
            opts="list get create delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__list)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get create delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__create)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help)
            opts="list get create delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__list)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help)
            opts="vacation imap pop language auto-forwarding filters forwarding-addresses delegates send-as help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__auto__subcmd__forwarding)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__auto__subcmd__forwarding__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__auto__subcmd__forwarding__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__delegates__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__filters__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__forwarding__subcmd__addresses__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__imap)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__imap__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__imap__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__language)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__language__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__language__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__pop)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__pop__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__pop__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as)
            opts="list get create update delete verify"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__send__subcmd__as__subcmd__verify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__vacation)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__vacation__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__help__subcmd__vacation__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__imap)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get set update help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help)
            opts="get set help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__help__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__set)
            opts="-c -a -b -h -V --enable --disable --auto-expunge --expunge-behavior --max-folder-size --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --auto-expunge)
                    COMPREPLY=($(compgen -W "true false" -- "${cur}"))
                    return 0
                    ;;
                --expunge-behavior)
                    COMPREPLY=($(compgen -W "archive trash deleteForever" -- "${cur}"))
                    return 0
                    ;;
                --max-folder-size)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__language)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get set update help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help)
            opts="get set help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__help__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__set)
            opts="-c -a -b -h -V --display-language --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --display-language)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__pop)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get set update help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help)
            opts="get set help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__help__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__set)
            opts="-c -a -b -h -V --access-window --disposition --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --access-window)
                    COMPREPLY=($(compgen -W "disabled fromNowOn allMail" -- "${cur}"))
                    return 0
                    ;;
                --disposition)
                    COMPREPLY=($(compgen -W "leaveInInbox archive trash markRead" -- "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get create update delete del remove rm verify help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__create)
            opts="-c -a -b -h -V --display-name --reply-to-address --signature --treat-as-alias --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --display-name)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --reply-to-address)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --signature)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help)
            opts="list get create update delete verify help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__help__subcmd__verify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__list)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__update)
            opts="-c -a -b -h -V --display-name --reply-to-address --signature --treat-as-alias --patch --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --display-name)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --reply-to-address)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --signature)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__verify)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get set update help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help)
            opts="get set help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__help__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__set)
            opts="-c -a -b -h -V --enable --disable --subject --body --html --restrict-to-contacts --restrict-to-domain --start-time --end-time --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --html)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --restrict-to-contacts)
                    COMPREPLY=($(compgen -W "true false" -- "${cur}"))
                    return 0
                    ;;
                --restrict-to-domain)
                    COMPREPLY=($(compgen -W "true false" -- "${cur}"))
                    return 0
                    ;;
                --start-time)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --end-time)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get modify trash untrash delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__get)
            opts="-c -a -b -h -V --format --header --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --format)
                    COMPREPLY=($(compgen -W "minimal full raw metadata" -- "${cur}"))
                    return 0
                    ;;
                --header)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__help)
            opts="list get modify trash untrash delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__modify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__trash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__help__subcmd__untrash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__list)
            opts="-q -l -s -c -a -b -h -V --query --label --max-results --page-token --include-spam-trash --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --query)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -q)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -l)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --max-results)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page-token)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__modify)
            opts="-c -a -b -h -V --add-label --remove-label --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --add-label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --remove-label)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__trash)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__gmail__subcmd__threads__subcmd__untrash)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help)
            opts="mailbox envelope flag message attachment imap jmap gmail msgraph m2dir smtp account completion manual json-schema help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__account)
            opts="list check"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__account__subcmd__check)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__account__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__attachment)
            opts="list download"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__attachment__subcmd__download)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__attachment__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__completion)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__envelope)
            opts="list search"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__envelope__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__envelope__subcmd__search)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__flag)
            opts="add set remove"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__flag__subcmd__add)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__flag__subcmd__remove)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__flag__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail)
            opts="profile labels messages attachments drafts threads history settings"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__attachments)
            opts="get"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__attachments__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__drafts)
            opts="list get create update send delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__drafts__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__history)
            opts="list"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__history__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__labels)
            opts="list get create update delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__labels__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages)
            opts="list get send import insert modify trash untrash delete batch-modify batch-delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__batch__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__batch__subcmd__modify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__import)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__insert)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__modify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__trash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__messages__subcmd__untrash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__profile)
            opts="get"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__profile__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings)
            opts="vacation imap pop language auto-forwarding filters forwarding-addresses delegates send-as"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__auto__subcmd__forwarding__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__delegates__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__filters__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__forwarding__subcmd__addresses__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__imap)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__imap__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__language)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__language__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__pop)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__pop__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as)
            opts="list get create update delete verify"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__send__subcmd__as__subcmd__verify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__vacation)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__settings__subcmd__vacation__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 6 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__threads)
            opts="list get modify trash untrash delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__modify)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__trash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__gmail__subcmd__threads__subcmd__untrash)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap)
            opts="id select create delete rename subscribe unsubscribe list status close unselect expunge search sort thread store flags fetch append copy move raw"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__append)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__close)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__expunge)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__fetch)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__flags)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__id)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__raw)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__rename)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__search)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__select)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__sort)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__status)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__store)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__subscribe)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__thread)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__unselect)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__imap__subcmd__unsubscribe)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap)
            opts="query mailbox email thread identity submission vacation-response"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email)
            opts="get query read update delete copy export import parse"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__export)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__import)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__parse)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__read)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__email__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__identity)
            opts="get create update delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__identity__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__identity__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__identity__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__identity__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox)
            opts="get query create update destroy"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__destroy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__mailbox__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__submission)
            opts="get query create cancel"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__submission__subcmd__cancel)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__submission__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__submission__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__submission__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__thread)
            opts="get"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__thread__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__vacation__subcmd__response)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__json__subcmd__schema)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir)
            opts="create delete list messages flags"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__flags)
            opts="list add set remove"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__flags__subcmd__add)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__flags__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__flags__subcmd__remove)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__flags__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__messages)
            opts="save"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__m2dir__subcmd__messages__subcmd__save)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__mailbox)
            opts="list"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__mailbox__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__manual)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__message)
            opts="add compose copy forward move read reply send"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__message__subcmd__add)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__message__subcmd__compose)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__message__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__message__subcmd__forward)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__message__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__message__subcmd__read)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__message__subcmd__reply)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__message__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph)
            opts="profile mail-folder message attachment"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__attachment__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder)
            opts="list child-folders get create rename copy move delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__child__subcmd__folders)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__rename)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__message)
            opts="list get create update send copy move delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__message__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__profile)
            opts="get"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__msgraph__subcmd__profile__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__smtp)
            opts="send raw"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__smtp__subcmd__raw)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__help__subcmd__smtp__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version id select create delete rename subscribe unsubscribe list status close unselect expunge search sort thread store flags fetch append copy move raw help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__append)
            opts="-f -c -a -b -h -V --flag --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --flag)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__close)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__copy)
            opts="-m -c -a -b -h -V --mailbox --no-select --seq --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__create)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__expunge)
            opts="-c -a -b -h -V --no-select --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__fetch)
            opts="-m -c -a -b -h -V --mailbox --no-select --envelope --structure --flags --internal-date --size --seq --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__flags)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help)
            opts="id select create delete rename subscribe unsubscribe list status close unselect expunge search sort thread store flags fetch append copy move raw help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__append)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__close)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__expunge)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__fetch)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__flags)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__id)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__raw)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__rename)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__search)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__select)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__sort)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__status)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__store)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__subscribe)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__thread)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__unselect)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__help__subcmd__unsubscribe)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__id)
            opts="-p -c -a -b -h -V --parameter --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --parameter)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -p)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__list)
            opts="-A -r -p -c -a -b -h -V --all --reference --pattern --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --reference)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -r)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --pattern)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -p)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__move)
            opts="-m -c -a -b -h -V --mailbox --no-select --seq --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__raw)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__rename)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__search)
            opts="-m -c -a -b -h -V --mailbox --no-select --from --to --cc --bcc --subject --body --text --before --since --on --larger --smaller --seen --unseen --flagged --unflagged --answered --unanswered --deleted --undeleted --draft --undraft --new --old --recent --seq --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --cc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --bcc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --text)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --before)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --since)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --on)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --larger)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --smaller)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__select)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__sort)
            opts="-m -S -r -c -a -b -h -V --mailbox --no-select --sort --reverse --from --to --cc --bcc --subject --body --text --before --since --on --larger --smaller --seen --unseen --flagged --unflagged --answered --unanswered --deleted --undeleted --draft --undraft --new --old --recent --seq --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --sort)
                    COMPREPLY=($(compgen -W "date arrival from to cc subject size" -- "${cur}"))
                    return 0
                    ;;
                -S)
                    COMPREPLY=($(compgen -W "date arrival from to cc subject size" -- "${cur}"))
                    return 0
                    ;;
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --cc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --bcc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --text)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --before)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --since)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --on)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --larger)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --smaller)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__status)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__store)
            opts="-m -f -c -a -b -h -V --mailbox --no-select --action --flag --seq --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --action)
                    COMPREPLY=($(compgen -W "add remove set" -- "${cur}"))
                    return 0
                    ;;
                --flag)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__subscribe)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__thread)
            opts="-m -A -c -a -b -h -V --mailbox --no-select --algorithm --from --to --cc --bcc --subject --body --text --before --since --on --larger --smaller --seen --unseen --flagged --unflagged --answered --unanswered --deleted --undeleted --draft --undraft --new --old --recent --seq --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --algorithm)
                    COMPREPLY=($(compgen -W "references orderedsubject" -- "${cur}"))
                    return 0
                    ;;
                -A)
                    COMPREPLY=($(compgen -W "references orderedsubject" -- "${cur}"))
                    return 0
                    ;;
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --cc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --bcc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --text)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --before)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --since)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --on)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --larger)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --smaller)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__unselect)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__imap__subcmd__unsubscribe)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version query mailbox mbox email thread identity submission vacation-response vacation help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get query read update delete copy export import parse help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__copy)
            opts="-c -a -b -h -V --from-account --mailbox-id --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --from-account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --mailbox-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__export)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help)
            opts="get query read update delete copy export import parse help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__export)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__import)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__parse)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__read)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__help__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__import)
            opts="-c -a -b -h -V --mailbox-id --keyword --received-at --upload-only --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --keyword)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --received-at)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__parse)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__query)
            opts="-m -s -p -c -a -b -h -V --mailbox --before --after --min-size --max-size --has-keyword --not-keyword --has-attachment --text --from --to --subject --body --sort --desc --page-size --page --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --before)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --after)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --min-size)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --max-size)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --has-keyword)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --not-keyword)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --text)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --sort)
                    COMPREPLY=($(compgen -W "received-at sent-at size from to subject has-attachment" -- "${cur}"))
                    return 0
                    ;;
                --page-size)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -p)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__read)
            opts="-c -a -b -h -V --html --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__email__subcmd__update)
            opts="-c -a -b -h -V --add-keyword --remove-keyword --keywords --add-mailbox --remove-mailbox --mailboxes --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --add-keyword)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --remove-keyword)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --keywords)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --add-mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --remove-mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --mailboxes)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help)
            opts="query mailbox email thread identity submission vacation-response help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email)
            opts="get query read update delete copy export import parse"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__export)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__import)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__parse)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__read)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__email__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__identity)
            opts="get create update delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__identity__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__identity__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__identity__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__identity__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox)
            opts="get query create update destroy"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__destroy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__mailbox__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__submission)
            opts="get query create cancel"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__submission__subcmd__cancel)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__submission__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__submission__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__submission__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__thread)
            opts="get"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__thread__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__vacation__subcmd__response)
            opts="get set"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__vacation__subcmd__response__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__help__subcmd__vacation__subcmd__response__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get create update delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__create)
            opts="-c -a -b -h -V --text-signature --html-signature --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --text-signature)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --html-signature)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__help)
            opts="get create update delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__help__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__identity__subcmd__update)
            opts="-c -a -b -h -V --name --text-signature --html-signature --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --name)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --text-signature)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --html-signature)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get query create add new update destroy delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__create)
            opts="-c -a -b -h -V --parent-id --subscribe --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --parent-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__destroy)
            opts="-c -a -b -h -V --purge --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help)
            opts="get query create update destroy help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__destroy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__help__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__query)
            opts="-s -p -c -a -b -h -V --parent-id --role --custom-role --name --subscribed --has-any-role --sort --desc --page-size --page --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --parent-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --role)
                    COMPREPLY=($(compgen -W "inbox archive drafts flagged important junk sent subscribed trash" -- "${cur}"))
                    return 0
                    ;;
                --custom-role)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --name)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --sort)
                    COMPREPLY=($(compgen -W "name sort-order parent-id" -- "${cur}"))
                    return 0
                    ;;
                --page-size)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -p)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__mailbox__subcmd__update)
            opts="-c -a -b -h -V --name --parent-id --role --custom-role --sort-order --subscribe --unsubscribe --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --name)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --parent-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --role)
                    COMPREPLY=($(compgen -W "inbox archive drafts flagged important junk sent subscribed trash" -- "${cur}"))
                    return 0
                    ;;
                --custom-role)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --sort-order)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__query)
            opts="-c -a -b -h -V --using --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --using)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get query create cancel help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__cancel)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__create)
            opts="-c -a -b -h -V --identity-id --mail-from --rcpt-to --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --identity-id)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --mail-from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --rcpt-to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__help)
            opts="get query create cancel help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__cancel)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__help__subcmd__query)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__submission__subcmd__query)
            opts="-s -p -c -a -b -h -V --undo-status --before --after --page-size --page --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --undo-status)
                    COMPREPLY=($(compgen -W "pending final canceled" -- "${cur}"))
                    return 0
                    ;;
                --before)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --after)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page-size)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --page)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -p)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__thread)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__thread__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__thread__subcmd__help)
            opts="get help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__thread__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__thread__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__vacation__subcmd__response)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get set help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help)
            opts="get set help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__help__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__jmap__subcmd__vacation__subcmd__response__subcmd__set)
            opts="-c -a -b -h -V --enable --disable --from-date --to-date --subject --text-body --html-body --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --from-date)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to-date)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --text-body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --html-body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__json__subcmd__schema)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version create delete list messages flags help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__create)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list add set remove help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__add)
            opts="-m -f -c -a -b -h -V --m2dir --flag --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --m2dir)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --flag)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__help)
            opts="list add set remove help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__add)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__remove)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__help__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__list)
            opts="-m -c -a -b -h -V --m2dir --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --m2dir)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__remove)
            opts="-m -f -c -a -b -h -V --m2dir --flag --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --m2dir)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --flag)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__flags__subcmd__set)
            opts="-m -f -c -a -b -h -V --m2dir --flag --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --m2dir)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --flag)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help)
            opts="create delete list messages flags help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__flags)
            opts="list add set remove"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__flags__subcmd__add)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__flags__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__flags__subcmd__remove)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__flags__subcmd__set)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__messages)
            opts="save"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__help__subcmd__messages__subcmd__save)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__list)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__messages)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version save help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__messages__subcmd__help)
            opts="save help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__messages__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__messages__subcmd__help__subcmd__save)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__m2dir__subcmd__messages__subcmd__save)
            opts="-m -f -c -a -b -h -V --m2dir --flag --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --m2dir)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --flag)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__mailbox)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list ls help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__mailbox__subcmd__help)
            opts="list help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__mailbox__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__mailbox__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__mailbox__subcmd__list)
            opts="-w -c -a -b -h -V --counts --max-width --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --max-width)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -w)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__manual)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version add save compose write copy cp forward fwd move mv read reply send help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__add)
            opts="-m -f -c -a -b -h -V --mailbox --flag --send --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --flag)
                    COMPREPLY=($(compgen -W "seen answered flagged draft" -- "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -W "seen answered flagged draft" -- "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__compose)
            opts="-t -s -c -a -b -h -V --from --to --cc --bcc --subject --body --body-file --attach --signature --signature-file --save --send --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -t)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --cc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --bcc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --attach)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --signature)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --signature-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --save)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__copy)
            opts="-f -t -c -a -b -h -V --from --to --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -t)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__forward)
            opts="-m -t -s -P -Q -c -a -b -h -V --mailbox --from --to --cc --bcc --subject --body --body-file --attach --signature --signature-file --posting-style --quote-headline --save --send --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -t)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --cc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --bcc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --attach)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --signature)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --signature-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --posting-style)
                    COMPREPLY=($(compgen -W "top bottom" -- "${cur}"))
                    return 0
                    ;;
                -P)
                    COMPREPLY=($(compgen -W "top bottom" -- "${cur}"))
                    return 0
                    ;;
                --quote-headline)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -Q)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --save)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help)
            opts="add compose copy forward move read reply send help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help__subcmd__add)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help__subcmd__compose)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help__subcmd__forward)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help__subcmd__read)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help__subcmd__reply)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__help__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__move)
            opts="-f -t -c -a -b -h -V --from --to --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -t)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__read)
            opts="-m -c -a -b -h -V --mailbox --raw --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__reply)
            opts="-m -t -s -P -Q -c -a -b -h -V --mailbox --from --to --cc --bcc --subject --body --body-file --attach --signature --signature-file --posting-style --quote-headline --save --send --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mailbox)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -m)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -t)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --cc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --bcc)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --subject)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -s)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --body-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --attach)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --signature)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --signature-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --posting-style)
                    COMPREPLY=($(compgen -W "top bottom" -- "${cur}"))
                    return 0
                    ;;
                -P)
                    COMPREPLY=($(compgen -W "top bottom" -- "${cur}"))
                    return 0
                    ;;
                --quote-headline)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -Q)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --save)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__message__subcmd__send)
            opts="-c -a -b -h -V --save --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --save)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version profile mail-folder mail-folders folder folders message messages msg attachment attachments help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get create delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__create)
            opts="-n -t -c -a -b -h -V --name --content-type --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --name)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -n)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --content-type)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -t)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__get)
            opts="-o -c -a -b -h -V --output --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --output)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -o)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help)
            opts="list get create delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__attachment__subcmd__list)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help)
            opts="profile mail-folder message attachment help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment)
            opts="list get create delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__attachment__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder)
            opts="list child-folders get create rename copy move delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__child__subcmd__folders)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__mail__subcmd__folder__subcmd__rename)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__message)
            opts="list get create update send copy move delete"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__message__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__profile)
            opts="get"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__help__subcmd__profile__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list child-folders children child get create rename copy move delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__child__subcmd__folders)
            opts="-c -a -b -h -V --top --skip --select --hidden --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --top)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --skip)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --select)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__copy)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__create)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help)
            opts="list child-folders get create rename copy move delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__child__subcmd__folders)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__help__subcmd__rename)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__list)
            opts="-c -a -b -h -V --top --skip --select --hidden --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --top)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --skip)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --select)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__move)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__mail__subcmd__folder__subcmd__rename)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version list get create update send copy move delete del remove rm help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__copy)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__create)
            opts="-f -c -a -b -h -V --folder --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --folder)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__delete)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__get)
            opts="-c -a -b -h -V --raw --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help)
            opts="list get create update send copy move delete help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__copy)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__create)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__delete)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__list)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__move)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__help__subcmd__update)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__list)
            opts="-f -c -a -b -h -V --folder --top --skip --filter --search --orderby --select --count --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --folder)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --top)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --skip)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --filter)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --search)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --orderby)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --select)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__move)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__send)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__message__subcmd__update)
            opts="-c -a -b -h -V --read --unread --importance --category --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --importance)
                    COMPREPLY=($(compgen -W "low normal high" -- "${cur}"))
                    return 0
                    ;;
                --category)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__profile)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version get help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__profile__subcmd__get)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__profile__subcmd__help)
            opts="get help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__profile__subcmd__help__subcmd__get)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__msgraph__subcmd__profile__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 5 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__smtp)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version send raw help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 2 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__smtp__subcmd__help)
            opts="send raw help"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__smtp__subcmd__help__subcmd__help)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__smtp__subcmd__help__subcmd__raw)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__smtp__subcmd__help__subcmd__send)
            opts=""
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 4 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__smtp__subcmd__raw)
            opts="-c -a -b -h -V --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
        himalaya__subcmd__smtp__subcmd__send)
            opts="-f -t -c -a -b -h -V --mail-from --rcpt-to --config --account --backend --json --log --log-level --log-file --help --version"
            if [[ ${cur} == -* || ${COMP_CWORD} -eq 3 ]] ; then
                COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                return 0
            fi
            case "${prev}" in
                --mail-from)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -f)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --rcpt-to)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -t)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --config)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -c)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --account)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                -a)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                --backend)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                -b)
                    COMPREPLY=($(compgen -W "auto imap jmap gmail msgraph maildir m2dir smtp" -- "${cur}"))
                    return 0
                    ;;
                --log-level)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log)
                    COMPREPLY=($(compgen -W "off error warn info debug trace" -- "${cur}"))
                    return 0
                    ;;
                --log-file)
                    COMPREPLY=($(compgen -f "${cur}"))
                    return 0
                    ;;
                *)
                    COMPREPLY=()
                    ;;
            esac
            COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
            return 0
            ;;
    esac
}

if [[ "${BASH_VERSINFO[0]}" -eq 4 && "${BASH_VERSINFO[1]}" -ge 4 || "${BASH_VERSINFO[0]}" -gt 4 ]]; then
    complete -F _himalaya -o nosort -o bashdefault -o default himalaya
else
    complete -F _himalaya -o bashdefault -o default himalaya
fi
