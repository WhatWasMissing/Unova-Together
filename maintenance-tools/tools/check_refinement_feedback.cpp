#include "ConnectionFeedback.h"
#include "Gen5Menu.h"
#include <cassert>
#include <iostream>
int main() {
    const QVariantMap local{{"fieldPositionOwned",true},{"cameraValid",true},{"map",191}};
    QVariantMap peer{{"active",true},{"map",191},{"modVersion","1.0.10"},{"romFingerprint","same"}};
    assert(PresenceVisibilityReason(local,peer,100,"1.0.10","same").contains("should be visible"));
    assert(PresenceVisibilityReason(local,peer,3000,"1.0.10","same").contains("fresh"));
    peer["map"]=192;assert(PresenceVisibilityReason(local,peer,100,"1.0.10","same").contains("Different maps"));
    peer["map"]=191;peer["modVersion"]="1.0.9";assert(PresenceVisibilityReason(local,peer,100,"1.0.10","same").contains("Different releases"));
    peer["modVersion"]="1.0.10";peer["romFingerprint"]="other";assert(PresenceVisibilityReason(local,peer,100,"1.0.10","same").contains("Different ROM"));
    peer["romFingerprint"]="same";peer["modVersion"]="1.0.7-dev";assert(PresenceVisibilityReason(local,peer,100,"1.0.10","same").contains("not reported reliably"));
    const auto before=peer;PresenceVisibilityReason(local,peer,100,"1.0.10","same");assert(peer==before);
    Gen5Menu menu;
    const QString message="Your companion listens carefully as you share a very long story about the paths you walked together. It remembers the forest, the bridge, the bustling town, and the quiet evening by the water. It gives you a reassuring nudge and waits for the next chapter.";
    const auto pages=menu.companionDialoguePages(message);assert(pages.size()>1);
    auto joined=pages.join(' ');joined.replace('\n',' ');assert(joined==message);
    for(const auto& page:pages) assert(page.split('\n').size()<=3);
    std::cout<<"Visibility reasons are read-only; long companion replies retain all words across pages.\n";
}
