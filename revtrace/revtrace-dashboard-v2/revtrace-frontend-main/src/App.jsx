import { useEffect, useMemo, useRef, useState } from "react";
import styles from "./App.module.css";

const CORE_URL = "http://127.0.0.1:8100";

const navigation = [
  { icon: "⌂", label: "Dashboard", page: "dashboard" },
  { icon: "◎", label: "Accounts / Pipeline", page: "accounts" },
  { icon: "♙", label: "Prospecting", external: "http://localhost:8501" },
  { icon: "$", label: "Deal Desk", external: "http://localhost:3000" },
  { icon: "▤", label: "Proposals / RFP", external: "http://localhost:8502" },
];

const secondaryNavigation = [
  { icon: "◉", label: "Memory", page: "memory" },
  { icon: "▥", label: "Analytics", page: "analytics" },
];

const STAGE_ORDER = [
  "NEW_PROSPECT",
  "OUTREACH_SENT",
  "ENGAGED_PROSPECT",
  "MEETING_SCHEDULED",
  "QUALIFIED_OPPORTUNITY",
  "DEAL_DESK",
  "COMMERCIAL_APPROVED",
  "PROPOSAL_DRAFT",
  "PROPOSAL_SUBMITTED",
  "WON",
  "LOST",
];

const JOURNEY_STEPS = [
  { label: "Prospect", stage: "NEW_PROSPECT" },
  { label: "Outreach", stage: "OUTREACH_SENT" },
  { label: "Reply", stage: "ENGAGED_PROSPECT" },
  { label: "Meeting", stage: "MEETING_SCHEDULED" },
  { label: "Qualified", stage: "QUALIFIED_OPPORTUNITY" },
  { label: "Deal Desk", stage: "DEAL_DESK" },
  { label: "Proposal", stage: "PROPOSAL_DRAFT" },
  { label: "Won / Lost", stage: "WON" },
];

function formatStage(value) {
  if (!value) return "Unknown";

  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    );
}

function formatTime(value) {
  if (!value) return "";

  try {
    return new Date(
      value
    ).toLocaleString(
      [],
      {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  } catch {
    return value;
  }
}

function journeyState(
  currentStage,
  stepStage
) {
  if (
    currentStage === "WON" ||
    currentStage === "LOST"
  ) {
    return "done";
  }

  const currentIndex =
    STAGE_ORDER.indexOf(
      currentStage
    );

  const stepIndex =
    STAGE_ORDER.indexOf(
      stepStage
    );

  if (currentIndex === -1) {
    return "next";
  }

  if (stepIndex < currentIndex) {
    return "done";
  }

  if (stepIndex === currentIndex) {
    return "current";
  }

  return "next";
}

function App() {
  const [
    activePage,
    setActivePage,
  ] = useState(
    "dashboard"
  );

  const [
    accounts,
    setAccounts,
  ] = useState([]);

  const [
    selectedAccountId,
    setSelectedAccountId,
  ] = useState(null);

  const [
    accountDetail,
    setAccountDetail,
  ] = useState(null);

  const [
    memoryData,
    setMemoryData,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    searchFocused,
    setSearchFocused,
  ] = useState(false);

  const selectedAccountRef =
    useRef(null);

  useEffect(
    () => {
      selectedAccountRef.current =
        selectedAccountId;

      if (
        selectedAccountId
      ) {
        window.localStorage.setItem(
          "revtrace-dashboard-account",
          selectedAccountId
        );
      }
    },
    [
      selectedAccountId,
    ]
  );

  async function fetchAccounts(
    preserveSelection = true
  ) {
    try {
      setError("");

      const response =
        await fetch(
          `${CORE_URL}/accounts`,
          {
            cache:
              "no-store",
          }
        );

      if (!response.ok) {
        throw new Error(
          `RevTrace Core returned ${response.status}`
        );
      }

      const data =
        await response.json();

      const incoming =
        Array.isArray(data)
          ? data
          : data.accounts || [];

      const sorted =
        [...incoming].sort(
          (a, b) =>
            new Date(
              b.updated_at ||
                b.created_at ||
                0
            ).getTime() -
            new Date(
              a.updated_at ||
                a.created_at ||
                0
            ).getTime()
        );

      setAccounts(
        sorted
      );

      if (
        sorted.length === 0
      ) {
        setSelectedAccountId(
          null
        );

        setAccountDetail(
          null
        );

        return sorted;
      }

      setSelectedAccountId(
        (current) => {
          if (
            preserveSelection &&
            current &&
            sorted.some(
              (account) =>
                account.account_id ===
                current
            )
          ) {
            return current;
          }

          const stored =
            window.localStorage.getItem(
              "revtrace-dashboard-account"
            );

          if (
            stored &&
            sorted.some(
              (account) =>
                account.account_id ===
                stored
            )
          ) {
            return stored;
          }

          return (
            sorted[0]
              ?.account_id ||
            null
          );
        }
      );

      return sorted;
    } catch (err) {
      setError(
        err?.message ||
          "Unable to load accounts."
      );

      return [];
    } finally {
      setLoading(
        false
      );
    }
  }

  async function fetchAccountDetail(
    accountId
  ) {
    if (!accountId) {
      setAccountDetail(
        null
      );
      return;
    }

    try {
      const response =
        await fetch(
          `${CORE_URL}/accounts/${accountId}`,
          {
            cache:
              "no-store",
          }
        );

      if (!response.ok) {
        throw new Error(
          `Account request returned ${response.status}`
        );
      }

      const data =
        await response.json();

      if (
        selectedAccountRef.current &&
        selectedAccountRef.current !==
          accountId
      ) {
        return;
      }

      setAccountDetail(
        data
      );
    } catch (err) {
      setError(
        err?.message ||
          "Unable to load account details."
      );
    }
  }

  async function fetchMemory(
    accountId
  ) {
    if (!accountId) {
      setMemoryData(
        null
      );
      return;
    }

    try {
      setError("");

      setMemoryData(
        null
      );

      /*
       * IMPORTANT
       *
       * Do not call:
       *
       * /accounts/{id}/memory
       *
       * The Memory page uses the canonical
       * RevTrace Core journey directly.
       * This prevents the UI hanging while
       * waiting for an external Hindsight
       * recall request.
       */
      const response =
        await fetch(
          `${CORE_URL}/accounts/${accountId}`,
          {
            cache:
              "no-store",
          }
        );

      if (!response.ok) {
        throw new Error(
          `Memory trace request returned ${response.status}`
        );
      }

      const data =
        await response.json();

      setMemoryData({
        account:
          data.account ||
          null,

        events:
          Array.isArray(
            data.events
          )
            ? data.events
            : [],

        provider:
          "Hindsight Cloud",

        source:
          "RevTrace Shared Revenue Memory",

        status:
          "CONNECTED",
      });
    } catch (err) {
      const message =
        err?.message ||
        "Unable to load memory trace.";

      setMemoryData({
        account:
          null,

        events:
          [],

        provider:
          "Hindsight Cloud",

        source:
          "RevTrace Shared Revenue Memory",

        status:
          "ERROR",

        error:
          message,
      });

      setError(
        message
      );
    }
  }

  async function refreshEverything() {
    const list =
      await fetchAccounts(
        true
      );

    const current =
      selectedAccountRef.current;

    if (
      current &&
      list.some(
        (account) =>
          account.account_id ===
          current
      )
    ) {
      await fetchAccountDetail(
        current
      );

      if (
        activePage ===
        "memory"
      ) {
        await fetchMemory(
          current
        );
      }
    }
  }

  useEffect(
    () => {
      fetchAccounts(
        true
      );
    },
    []
  );

  useEffect(
    () => {
      if (
        selectedAccountId
      ) {
        fetchAccountDetail(
          selectedAccountId
        );
      }
    },
    [
      selectedAccountId,
    ]
  );

  useEffect(
    () => {
      const interval =
        window.setInterval(
          async () => {
            const list =
              await fetchAccounts(
                true
              );

            const current =
              selectedAccountRef.current;

            if (
              current &&
              list.some(
                (account) =>
                  account.account_id ===
                  current
              )
            ) {
              await fetchAccountDetail(
                current
              );
            }
          },
          5000
        );

      return () =>
        window.clearInterval(
          interval
        );
    },
    []
  );

  useEffect(
    () => {
      function handleFocus() {
        refreshEverything();
      }

      window.addEventListener(
        "focus",
        handleFocus
      );

      return () =>
        window.removeEventListener(
          "focus",
          handleFocus
        );
    },
    [
      activePage,
    ]
  );

  useEffect(
    () => {
      if (
        activePage ===
          "memory" &&
        selectedAccountId
      ) {
        fetchMemory(
          selectedAccountId
        );
      }
    },
    [
      activePage,
      selectedAccountId,
    ]
  );

  function navigate(
    item
  ) {
    if (
      item.external
    ) {
      window.open(
        item.external,
        "_blank"
      );

      return;
    }

    if (
      item.page
    ) {
      setActivePage(
        item.page
      );
    }
  }

  function createNewProspect() {
    window.open(
      "http://localhost:8501",
      "_blank"
    );
  }

  function selectAccount(
    accountId,
    destination =
      "dashboard"
  ) {
    if (!accountId) {
      return;
    }

    setAccountDetail(
      null
    );

    setMemoryData(
      null
    );

    setSelectedAccountId(
      accountId
    );

    setActivePage(
      destination
    );
  }

  const selectedAccount =
    accountDetail?.account ||
    accounts.find(
      (account) =>
        account.account_id ===
        selectedAccountId
    ) ||
    null;

  const events =
    accountDetail?.events ||
    [];

  const latestEvents =
    useMemo(
      () =>
        [...events]
          .sort(
            (a, b) =>
              new Date(
                b.created_at ||
                  0
              ) -
              new Date(
                a.created_at ||
                  0
              )
          )
          .slice(
            0,
            6
          ),
      [
        events,
      ]
    );

  const searchResults =
    useMemo(
      () => {
        const term =
          search
            .trim()
            .toLowerCase();

        if (!term) {
          return [];
        }

        return accounts
          .filter(
            (account) =>
              [
                account.company,
                account.contact_name,
                account.industry,
                account.role,
                account.account_id,
                account.opportunity_id,
                account.stage,
                account.current_agent,
              ]
                .filter(Boolean)
                .join(" ")
                .toLowerCase()
                .includes(
                  term
                )
          )
          .slice(
            0,
            8
          );
      },
      [
        accounts,
        search,
      ]
    );

  const filteredAccounts =
    useMemo(
      () => {
        const term =
          search
            .trim()
            .toLowerCase();

        if (!term) {
          return accounts;
        }

        return accounts.filter(
          (account) =>
            [
              account.company,
              account.contact_name,
              account.industry,
              account.role,
              account.account_id,
              account.opportunity_id,
              account.stage,
              account.current_agent,
            ]
              .filter(Boolean)
              .join(" ")
              .toLowerCase()
              .includes(
                term
              )
        );
      },
      [
        accounts,
        search,
      ]
    );

  const stats =
    useMemo(
      () => {
        const prospects =
          accounts.filter(
            (account) =>
              [
                "NEW_PROSPECT",
                "OUTREACH_SENT",
                "ENGAGED_PROSPECT",
              ].includes(
                account.stage
              )
          ).length;

        const meetings =
          accounts.filter(
            (account) =>
              account.stage ===
              "MEETING_SCHEDULED"
          ).length;

        const activeDeals =
          accounts.filter(
            (account) =>
              [
                "QUALIFIED_OPPORTUNITY",
                "DEAL_DESK",
                "COMMERCIAL_APPROVED",
                "PROPOSAL_DRAFT",
                "PROPOSAL_SUBMITTED",
              ].includes(
                account.stage
              )
          ).length;

        const won =
          accounts.filter(
            (account) =>
              account.stage ===
              "WON"
          ).length;

        const lost =
          accounts.filter(
            (account) =>
              account.stage ===
              "LOST"
          ).length;

        return {
          prospects,
          meetings,
          activeDeals,
          won,
          lost,
        };
      },
      [
        accounts,
      ]
    );

  const pipeline =
    useMemo(
      () => [
        {
          label:
            "Prospects",

          value:
            stats.prospects,

          tone:
            "blue",
        },

        {
          label:
            "Meetings",

          value:
            stats.meetings,

          tone:
            "orange",
        },

        {
          label:
            "Qualified",

          value:
            accounts.filter(
              (account) =>
                account.stage ===
                "QUALIFIED_OPPORTUNITY"
            ).length,

          tone:
            "purple",
        },

        {
          label:
            "Deal Desk",

          value:
            accounts.filter(
              (account) =>
                [
                  "DEAL_DESK",
                  "COMMERCIAL_APPROVED",
                ].includes(
                  account.stage
                )
            ).length,

          tone:
            "violet",
        },

        {
          label:
            "Proposals",

          value:
            accounts.filter(
              (account) =>
                [
                  "PROPOSAL_DRAFT",
                  "PROPOSAL_SUBMITTED",
                ].includes(
                  account.stage
                )
            ).length,

          tone:
            "green",
        },

        {
          label:
            "Won",

          value:
            stats.won,

          tone:
            "success",
        },
      ],
      [
        accounts,
        stats,
      ]
    );

  const findLatestEvent =
    (type) =>
      [...events]
        .sort(
          (a, b) =>
            new Date(
              b.created_at ||
                0
            ) -
            new Date(
              a.created_at ||
                0
            )
        )
        .find(
          (event) =>
            event.event_type ===
            type
        );

  const prospectAnalysis =
    findLatestEvent(
      "PROSPECT_ANALYZED"
    );

  const outreachOutcome =
    findLatestEvent(
      "OUTREACH_OUTCOME"
    );

  const meetingCompleted =
    findLatestEvent(
      "MEETING_COMPLETED"
    );

  const commercialDecision =
    findLatestEvent(
      "COMMERCIAL_DECISION"
    );

  const proposalGenerated =
    findLatestEvent(
      "PROPOSAL_GENERATED"
    );

  const proposalSubmitted =
    findLatestEvent(
      "PROPOSAL_SUBMITTED"
    );

  const finalOutcome =
    findLatestEvent(
      "FINAL_OUTCOME"
    );

  const journeySteps =
    selectedAccount
      ? JOURNEY_STEPS.map(
          (step) => ({
            ...step,

            state:
              step.label ===
                "Won / Lost" &&
              [
                "WON",
                "LOST",
              ].includes(
                selectedAccount.stage
              )
                ? "done"
                : journeyState(
                    selectedAccount.stage,
                    step.stage
                  ),
          })
        )
      : [];

  return (
    <div
      className={
        styles.app
      }
    >

      <aside
        className={
          styles.sidebar
        }
      >

        <button
          className={
            styles.logoButton
          }
          onClick={() =>
            setActivePage(
              "dashboard"
            )
          }
        >
          <div
            className={
              styles.logoMark
            }
          >
            <span />
            <span />
            <span />
          </div>

          <span
            className={
              styles.logoText
            }
          >
            REV
            <span>
              TRACE
            </span>
          </span>
        </button>

        <nav
          className={
            styles.navigation
          }
        >

          {navigation.map(
            (item) => (
              <button
                key={
                  item.label
                }
                onClick={() =>
                  navigate(
                    item
                  )
                }
                className={`${styles.navItem} ${
                  item.page ===
                  activePage
                    ? styles.activeNav
                    : ""
                }`}
              >
                <span
                  className={
                    styles.icon
                  }
                >
                  {
                    item.icon
                  }
                </span>

                <span>
                  {
                    item.label
                  }
                </span>

                {item.external && (
                  <span
                    className={
                      styles.externalMark
                    }
                  >
                    ↗
                  </span>
                )}
              </button>
            )
          )}

          <div
            className={
              styles.divider
            }
          />

          {secondaryNavigation.map(
            (item) => (
              <button
                key={
                  item.label
                }
                onClick={() =>
                  navigate(
                    item
                  )
                }
                className={`${styles.navItem} ${
                  item.page ===
                  activePage
                    ? styles.activeNav
                    : ""
                }`}
              >
                <span
                  className={
                    styles.icon
                  }
                >
                  {
                    item.icon
                  }
                </span>

                <span>
                  {
                    item.label
                  }
                </span>
              </button>
            )
          )}

        </nav>

        <div
          className={
            styles.sidebarBottom
          }
        >

          <button
            className={
              styles.navItem
            }
            onClick={
              refreshEverything
            }
          >
            <span
              className={
                styles.icon
              }
            >
              ↻
            </span>

            <span>
              Refresh Data
            </span>
          </button>

          <div
            className={
              styles.memoryStatus
            }
          >
            <div
              className={
                styles.memoryIcon
              }
            >
              ◉
            </div>

            <div
              className={
                styles.memoryInfo
              }
            >
              <strong>
                Hindsight Connected
              </strong>

              <span>
                Shared revenue memory
              </span>
            </div>
          </div>

        </div>

      </aside>

      <main
        className={
          styles.main
        }
      >

        <header
          className={
            styles.topBar
          }
        >

          <div
            className={
              styles.searchWrapper
            }
          >

            <div
              className={
                styles.searchBox
              }
            >
              <span
                className={
                  styles.searchIcon
                }
              >
                ⌕
              </span>

              <input
                value={
                  search
                }
                onChange={
                  (event) =>
                    setSearch(
                      event.target.value
                    )
                }
                onFocus={() =>
                  setSearchFocused(
                    true
                  )
                }
                onBlur={() =>
                  window.setTimeout(
                    () =>
                      setSearchFocused(
                        false
                      ),
                    150
                  )
                }
                placeholder="Search company, contact, ACC-, OPP-, stage or agent..."
              />

              <span
                className={
                  styles.shortcut
                }
              >
                LIVE
              </span>
            </div>

            {searchFocused &&
              search.trim() && (
              <div
                className={
                  styles.searchResults
                }
              >

                {searchResults.length >
                0 ? (
                  searchResults.map(
                    (account) => (
                      <button
                        key={
                          account.account_id
                        }
                        className={
                          styles.searchResult
                        }
                        onMouseDown={
                          (event) =>
                            event.preventDefault()
                        }
                        onClick={() => {
                          selectAccount(
                            account.account_id,
                            "dashboard"
                          );

                          setSearch(
                            ""
                          );

                          setSearchFocused(
                            false
                          );
                        }}
                      >
                        <div>
                          <strong>
                            {
                              account.company
                            }
                          </strong>

                          <span>
                            {
                              account.account_id
                            }

                            {account.opportunity_id
                              ? ` · ${account.opportunity_id}`
                              : ""}
                          </span>
                        </div>

                        <div
                          className={
                            styles.searchResultRight
                          }
                        >
                          <strong>
                            {formatStage(
                              account.stage
                            )}
                          </strong>

                          <span>
                            {formatStage(
                              account.current_agent
                            )}
                          </span>
                        </div>
                      </button>
                    )
                  )
                ) : (
                  <div
                    className={
                      styles.noSearchResults
                    }
                  >
                    No matching RevTrace account.
                  </div>
                )}

              </div>
            )}

          </div>

          <div
            className={
              styles.topRight
            }
          >
            <button
              className={
                styles.refreshButton
              }
              onClick={
                refreshEverything
              }
              title="Refresh"
            >
              ↻
            </button>

            <div
              className={
                styles.profile
              }
            >
              <div
                className={
                  styles.avatar
                }
              >
                R
              </div>

              <div
                className={
                  styles.profileText
                }
              >
                <strong>
                  Revenue Team
                </strong>

                <span>
                  RevTrace Workspace
                </span>
              </div>
            </div>
          </div>

        </header>

        <div
          className={
            styles.content
          }
        >

          {error && (
            <div
              className={
                styles.errorBanner
              }
            >
              <strong>
                RevTrace Core:
              </strong>

              {" "}

              {error}
            </div>
          )}

          {activePage ===
            "dashboard" && (
            <DashboardPage
              allAccounts={
                accounts
              }
              selectedAccount={
                selectedAccount
              }
              selectedAccountId={
                selectedAccountId
              }
              selectAccount={
                selectAccount
              }
              events={
                events
              }
              latestEvents={
                latestEvents
              }
              stats={
                stats
              }
              pipeline={
                pipeline
              }
              journeySteps={
                journeySteps
              }
              prospectAnalysis={
                prospectAnalysis
              }
              outreachOutcome={
                outreachOutcome
              }
              meetingCompleted={
                meetingCompleted
              }
              commercialDecision={
                commercialDecision
              }
              proposalGenerated={
                proposalGenerated
              }
              proposalSubmitted={
                proposalSubmitted
              }
              finalOutcome={
                finalOutcome
              }
              createNewProspect={
                createNewProspect
              }
              refreshEverything={
                refreshEverything
              }
              loading={
                loading
              }
              setActivePage={
                setActivePage
              }
            />
          )}

          {activePage ===
            "accounts" && (
            <AccountsPage
              accounts={
                filteredAccounts
              }
              selectedAccountId={
                selectedAccountId
              }
              selectAccount={
                selectAccount
              }
              createNewProspect={
                createNewProspect
              }
            />
          )}

          {activePage ===
            "memory" && (
            <MemoryPage
              accounts={
                accounts
              }
              selectedAccountId={
                selectedAccountId
              }
              selectAccount={
                selectAccount
              }
              selectedAccount={
                selectedAccount
              }
              memoryData={
                memoryData
              }
              refresh={() =>
                fetchMemory(
                  selectedAccountId
                )
              }
            />
          )}

          {activePage ===
            "analytics" && (
            <AnalyticsPage
              accounts={
                accounts
              }
              stats={
                stats
              }
              pipeline={
                pipeline
              }
            />
          )}

        </div>

      </main>

    </div>
  );
}

function DashboardPage({
  allAccounts,
  selectedAccount,
  selectedAccountId,
  selectAccount,
  events,
  latestEvents,
  stats,
  pipeline,
  journeySteps,
  prospectAnalysis,
  outreachOutcome,
  meetingCompleted,
  commercialDecision,
  proposalGenerated,
  proposalSubmitted,
  finalOutcome,
  createNewProspect,
  refreshEverything,
  loading,
  setActivePage,
}) {
  return (
    <>

      <section
        className={
          styles.pageHeader
        }
      >
        <div>
          <span
            className={
              styles.eyebrow
            }
          >
            REVENUE COMMAND CENTER
          </span>

          <h1>
            From first outreach
            to closed revenue.
          </h1>

          <p>
            Every prospect,
            meeting,
            commercial decision
            and proposal shares
            one continuous
            Hindsight-powered
            customer journey.
          </p>
        </div>

        <button
          className={
            styles.newRequest
          }
          onClick={
            createNewProspect
          }
        >
          ＋ New Prospect
        </button>
      </section>

      <section
        className={
          styles.kpiGrid
        }
      >
        <KpiCard
          icon="♙"
          value={
            stats.prospects
          }
          label="Active Prospects"
          sub="Live from RevTrace Core"
          color="blue"
        />

        <KpiCard
          icon="◷"
          value={
            stats.meetings
          }
          label="Upcoming Meetings"
          sub="Current pipeline"
          color="orange"
        />

        <KpiCard
          icon="$"
          value={
            stats.activeDeals
          }
          label="Active Deals"
          sub="Qualified through proposal"
          color="purple"
        />

        <KpiCard
          icon="✓"
          value={
            stats.won
          }
          label="Won Deals"
          sub="Completed revenue journeys"
          color="green"
        />
      </section>

      <section
        className={
          styles.pipelineCard
        }
      >
        <div
          className={
            styles.cardHeaderRow
          }
        >
          <div>
            <h2>
              Revenue Pipeline
            </h2>

            <p>
              Live pipeline calculated
              from every RevTrace account.
            </p>
          </div>

          <span
            className={
              styles.liveBadge
            }
          >
            ● LIVE CORE DATA
          </span>
        </div>

        <div
          className={
            styles.pipelineGrid
          }
        >
          {pipeline.map(
            (
              item,
              index
            ) => (
              <div
                key={
                  item.label
                }
                className={
                  styles.pipelineItem
                }
              >
                <div
                  className={`${styles.pipelineBubble} ${styles[item.tone]}`}
                >
                  {
                    item.value
                  }
                </div>

                <strong>
                  {
                    item.label
                  }
                </strong>

                {index <
                  pipeline.length -
                    1 && (
                  <span
                    className={
                      styles.pipelineArrow
                    }
                  >
                    →
                  </span>
                )}
              </div>
            )
          )}
        </div>
      </section>

      <section
        className={
          styles.dashboardGrid
        }
      >

        <div
          className={
            styles.accountCard
          }
        >

          <div
            className={
              styles.cardHeaderRow
            }
          >

            <div>
              <span
                className={
                  styles.eyebrow
                }
              >
                LIVE ACCOUNT JOURNEY
              </span>

              <h2
                className={
                  styles.accountName
                }
              >
                {selectedAccount
                  ?.company ||
                  (loading
                    ? "Loading..."
                    : "No accounts yet")}
              </h2>

              {selectedAccount && (
                <p>
                  {
                    selectedAccount.industry ||
                    "Industry not specified"
                  }
                  {" · "}
                  {
                    selectedAccount.role ||
                    "Role not specified"
                  }
                  {" · "}
                  {
                    selectedAccount.account_id
                  }
                </p>
              )}
            </div>

            {selectedAccount && (
              <span
                className={`${styles.stageBadge} ${
                  selectedAccount.stage ===
                  "LOST"
                    ? styles.lostBadge
                    : ""
                }`}
              >
                {formatStage(
                  selectedAccount.stage
                )}
              </span>
            )}
          </div>

          {allAccounts.length >
            0 && (
            <div
              className={
                styles.accountSelectorRow
              }
            >
              <label>
                Account
              </label>

              <select
                value={
                  selectedAccountId ||
                  ""
                }
                onChange={
                  (event) =>
                    selectAccount(
                      event.target.value,
                      "dashboard"
                    )
                }
              >
                {allAccounts.map(
                  (account) => (
                    <option
                      key={
                        account.account_id
                      }
                      value={
                        account.account_id
                      }
                    >
                      {
                        account.company
                      }
                      {" — "}
                      {formatStage(
                        account.stage
                      )}
                    </option>
                  )
                )}
              </select>
            </div>
          )}

          {selectedAccount ? (
            <>

              <div
                className={
                  styles.journeyTrack
                }
              >
                {journeySteps.map(
                  (
                    step,
                    index
                  ) => (
                    <div
                      className={
                        styles.journeyStep
                      }
                      key={
                        step.label
                      }
                    >
                      <div
                        className={`${styles.stepCircle} ${styles[step.state]}`}
                      >
                        {step.state ===
                        "done"
                          ? "✓"
                          : index + 1}
                      </div>

                      <span>
                        {
                          step.label
                        }
                      </span>

                      {index <
                        journeySteps.length -
                          1 && (
                        <div
                          className={`${styles.stepLine} ${
                            step.state ===
                            "done"
                              ? styles.stepLineDone
                              : ""
                          }`}
                        />
                      )}
                    </div>
                  )
                )}
              </div>

              <div
                className={
                  styles.accountDetailGrid
                }
              >

                <div
                  className={
                    styles.contextPanel
                  }
                >
                  <h3>
                    Journey Context
                  </h3>

                  <ContextRow
                    label="Prospecting strategy"
                    value={
                      prospectAnalysis
                        ?.payload
                        ?.recommended_angle ||
                      "Waiting"
                    }
                  />

                  <ContextRow
                    label="Outreach outcome"
                    value={
                      outreachOutcome
                        ?.payload
                        ?.outcome ||
                      "Waiting"
                    }
                  />

                  <ContextRow
                    label="Discovery meeting"
                    value={
                      meetingCompleted
                        ? "Completed"
                        : "Waiting"
                    }
                  />

                  <ContextRow
                    label="Approved terms"
                    value={
                      commercialDecision
                        ?.payload
                        ?.finalTerms ||
                      "Waiting"
                    }
                  />

                  <ContextRow
                    label="Proposal draft"
                    value={
                      proposalGenerated
                        ? "Generated"
                        : "Waiting"
                    }
                  />

                  <ContextRow
                    label="Proposal"
                    value={
                      proposalSubmitted
                        ? "Submitted"
                        : "Waiting"
                    }
                  />

                  <ContextRow
                    label="Final outcome"
                    value={
                      finalOutcome
                        ?.payload
                        ?.outcome ||
                      formatStage(
                        selectedAccount.stage
                      )
                    }
                    strong
                  />
                </div>

                <div
                  className={
                    styles.memoryPanel
                  }
                >
                  <div
                    className={
                      styles.memoryPanelTitle
                    }
                  >
                    <span>
                      ◉
                    </span>

                    <div>
                      <strong>
                        Shared Journey Memory
                      </strong>

                      <small>
                        Hindsight Cloud
                      </small>
                    </div>
                  </div>

                  <div
                    className={
                      styles.memoryStatRow
                    }
                  >
                    <span>
                      Journey Events
                    </span>

                    <strong>
                      {
                        events.length
                      }
                    </strong>
                  </div>

                  <div
                    className={
                      styles.memoryStatRow
                    }
                  >
                    <span>
                      Current Owner
                    </span>

                    <strong>
                      {formatStage(
                        selectedAccount.current_agent
                      )}
                    </strong>
                  </div>

                  <div
                    className={
                      styles.memoryStatRow
                    }
                  >
                    <span>
                      Opportunity
                    </span>

                    <strong>
                      {selectedAccount.opportunity_id ||
                        "Not created yet"}
                    </strong>
                  </div>

                  <button
                    className={
                      styles.memoryButton
                    }
                    onClick={() =>
                      setActivePage(
                        "memory"
                      )
                    }
                  >
                    Open Memory Trace →
                  </button>
                </div>

              </div>

            </>
          ) : (
            <EmptyState
              title="No accounts yet"
              text="Create your first prospect and it will automatically appear here."
              action={
                createNewProspect
              }
            />
          )}

        </div>

        <div
          className={
            styles.activityCard
          }
        >
          <div
            className={
              styles.activityHeader
            }
          >
            <h2>
              Recent Activity
            </h2>

            <button
              onClick={
                refreshEverything
              }
            >
              Refresh →
            </button>
          </div>

          {latestEvents.length >
          0 ? (
            <div
              className={
                styles.activityList
              }
            >
              {latestEvents.map(
                (event) => (
                  <ActivityItem
                    key={
                      event.event_id
                    }
                    event={
                      event
                    }
                  />
                )
              )}
            </div>
          ) : (
            <p
              className={
                styles.mutedText
              }
            >
              No account events yet.
            </p>
          )}
        </div>

      </section>

      <section
        className={
          styles.agentSection
        }
      >
        <div
          className={
            styles.cardHeaderRow
          }
        >
          <div>
            <h2>
              Specialized Agents.
              One Revenue Journey.
            </h2>

            <p>
              The same account identity
              moves through each specialist
              agent while shared memory
              follows the customer.
            </p>
          </div>
        </div>

        <div
          className={
            styles.agentFlowGrid
          }
        >

          <AgentStage
            number="01"
            type="blue"
            title="Prospecting Agent"
            purpose="Get the conversation started"
            items={[
              "Recall similar prospects",
              "Recommend outreach angle",
              "Generate personalized message",
              "Qualify opportunity",
            ]}
            output="Qualified Opportunity"
            onClick={() =>
              window.open(
                "http://localhost:8501",
                "_blank"
              )
            }
          />

          <div
            className={
              styles.bigArrow
            }
          >
            →
          </div>

          <AgentStage
            number="02"
            type="purple"
            title="Deal Desk Agent"
            purpose="Decide acceptable commercial terms"
            items={[
              "Recall commercial precedents",
              "Evaluate exception",
              "Detect outliers",
              "Human approval",
            ]}
            output="Commercial Approval"
            onClick={() =>
              window.open(
                "http://localhost:3000",
                "_blank"
              )
            }
          />

          <div
            className={
              styles.bigArrow
            }
          >
            →
          </div>

          <AgentStage
            number="03"
            type="green"
            title="Proposal / RFP Agent"
            purpose="Create the formal customer offer"
            items={[
              "Extract RFP requirements",
              "Recall organizational knowledge",
              "Use approved commercial terms",
              "Generate grounded proposal",
            ]}
            output="Submitted Proposal"
            onClick={() =>
              window.open(
                "http://localhost:8502",
                "_blank"
              )
            }
          />

        </div>

        <div
          className={
            styles.memoryRibbon
          }
        >
          <span>
            ◉
          </span>

          <strong>
            Shared Hindsight Revenue Memory
          </strong>

          <span>
            Prospect →
            engagement →
            meeting →
            commercial decision →
            proposal →
            outcome
          </span>
        </div>
      </section>

    </>
  );
}

function AccountsPage({
  accounts,
  selectedAccountId,
  selectAccount,
  createNewProspect,
}) {
  return (
    <>

      <section
        className={
          styles.pageHeader
        }
      >
        <div>
          <span
            className={
              styles.eyebrow
            }
          >
            ACCOUNTS / PIPELINE
          </span>

          <h1>
            Every customer journey.
          </h1>

          <p>
            Every prospect created by
            the Prospecting Agent is
            synchronized here through
            RevTrace Core.
          </p>
        </div>

        <button
          className={
            styles.newRequest
          }
          onClick={
            createNewProspect
          }
        >
          ＋ New Prospect
        </button>
      </section>

      <div
        className={
          styles.tableCard
        }
      >
        <div
          className={
            styles.tableHeader
          }
        >
          <span>
            Company
          </span>

          <span>
            Contact
          </span>

          <span>
            Stage
          </span>

          <span>
            Current Agent
          </span>

          <span>
            Opportunity
          </span>

          <span>
            Updated
          </span>
        </div>

        {accounts.length >
        0 ? (
          accounts.map(
            (account) => (
              <button
                key={
                  account.account_id
                }
                className={`${styles.tableRow} ${
                  account.account_id ===
                  selectedAccountId
                    ? styles.selectedRow
                    : ""
                }`}
                onClick={() =>
                  selectAccount(
                    account.account_id,
                    "dashboard"
                  )
                }
              >
                <div>
                  <strong>
                    {
                      account.company
                    }
                  </strong>

                  <small>
                    {
                      account.account_id
                    }
                  </small>
                </div>

                <div>
                  {
                    account.contact_name ||
                    "—"
                  }

                  <small>
                    {
                      account.role ||
                      ""
                    }
                  </small>
                </div>

                <div>
                  <span
                    className={
                      styles.tableStage
                    }
                  >
                    {formatStage(
                      account.stage
                    )}
                  </span>
                </div>

                <div>
                  {formatStage(
                    account.current_agent
                  )}
                </div>

                <div>
                  {account.opportunity_id ||
                    "Not yet"}
                </div>

                <div>
                  {formatTime(
                    account.updated_at
                  )}
                </div>
              </button>
            )
          )
        ) : (
          <EmptyState
            title="No matching accounts"
            text="Create a prospect or clear your search."
            action={
              createNewProspect
            }
          />
        )}

      </div>

    </>
  );
}

function MemoryPage({
  accounts,
  selectedAccountId,
  selectAccount,
  selectedAccount,
  memoryData,
  refresh,
}) {
  const memoryEvents =
    memoryData?.events ||
    [];

  const sortedEvents =
    [...memoryEvents].sort(
      (a, b) =>
        new Date(
          b.created_at ||
            0
        ).getTime() -
        new Date(
          a.created_at ||
            0
        ).getTime()
    );

  const memoryStats = {
    total:
      memoryEvents.length,

    prospecting:
      memoryEvents.filter(
        (event) =>
          event.agent ===
          "PROSPECTING"
      ).length,

    dealDesk:
      memoryEvents.filter(
        (event) =>
          event.agent ===
          "DEAL_DESK"
      ).length,

    proposal:
      memoryEvents.filter(
        (event) =>
          event.agent ===
          "PROPOSAL_RFP"
      ).length,
  };

  function eventIcon(
    eventType = ""
  ) {
    if (
      eventType ===
      "PROSPECT_CREATED"
    ) {
      return "♙";
    }

    if (
      eventType ===
      "PROSPECT_ANALYZED"
    ) {
      return "◉";
    }

    if (
      eventType.includes(
        "OUTREACH"
      )
    ) {
      return "✉";
    }

    if (
      eventType.includes(
        "MEETING"
      )
    ) {
      return "◷";
    }

    if (
      eventType.includes(
        "COMMERCIAL"
      ) ||
      eventType.includes(
        "DEAL"
      )
    ) {
      return "$";
    }

    if (
      eventType.includes(
        "PROPOSAL"
      ) ||
      eventType.includes(
        "RFP"
      )
    ) {
      return "▤";
    }

    if (
      eventType ===
      "FINAL_OUTCOME"
    ) {
      return "✓";
    }

    return "•";
  }

  function memoryValue(
    value
  ) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "—";
    }

    if (
      typeof value ===
      "object"
    ) {
      return JSON.stringify(
        value
      );
    }

    return String(
      value
    );
  }

  return (
    <>

      <section
        className={
          styles.pageHeader
        }
      >
        <div>
          <span
            className={
              styles.eyebrow
            }
          >
            HINDSIGHT MEMORY
          </span>

          <h1>
            Account memory trace.
          </h1>

          <p>
            Follow everything RevTrace
            remembers about this customer
            across Prospecting, Deal Desk,
            Proposal / RFP and the final
            outcome.
          </p>
        </div>

        <button
          className={
            styles.secondaryButton
          }
          onClick={
            refresh
          }
        >
          ↻ Refresh Trace
        </button>
      </section>

      <section
        style={
          memoryShellStyle
        }
      >
        <div
          style={
            memorySelectorStyle
          }
        >
          <div>
            <span
              style={
                memoryLabelStyle
              }
            >
              Selected Account
            </span>

            <strong
              style={
                memoryAccountNameStyle
              }
            >
              {selectedAccount
                ?.company ||
                "No account selected"}
            </strong>

            {selectedAccount && (
              <span
                style={
                  memoryMetaStyle
                }
              >
                {
                  selectedAccount.account_id
                }
                {" · "}
                {formatStage(
                  selectedAccount.stage
                )}
                {" · "}
                {formatStage(
                  selectedAccount.current_agent
                )}
              </span>
            )}
          </div>

          <select
            value={
              selectedAccountId ||
              ""
            }
            onChange={
              (event) =>
                selectAccount(
                  event.target.value,
                  "memory"
                )
            }
            style={
              memorySelectStyle
            }
          >
            {accounts.map(
              (account) => (
                <option
                  key={
                    account.account_id
                  }
                  value={
                    account.account_id
                  }
                >
                  {
                    account.company
                  }
                  {" — "}
                  {formatStage(
                    account.stage
                  )}
                </option>
              )
            )}
          </select>
        </div>
      </section>

      <section
        style={
          memoryStatsGridStyle
        }
      >
        <MemoryStat
          label="Journey Memories"
          value={
            memoryStats.total
          }
          icon="◉"
        />

        <MemoryStat
          label="Prospecting"
          value={
            memoryStats.prospecting
          }
          icon="♙"
        />

        <MemoryStat
          label="Deal Desk"
          value={
            memoryStats.dealDesk
          }
          icon="$"
        />

        <MemoryStat
          label="Proposal / RFP"
          value={
            memoryStats.proposal
          }
          icon="▤"
        />
      </section>

      <section
        style={
          memoryProviderStyle
        }
      >
        <div
          style={{
            display:
              "flex",

            alignItems:
              "center",

            gap:
              12,
          }}
        >
          <span
            style={
              memoryProviderIconStyle
            }
          >
            ◉
          </span>

          <div>
            <strong
              style={{
                display:
                  "block",

                fontSize:
                  13,
              }}
            >
              {memoryData
                ?.provider ||
                "Hindsight Cloud"}
            </strong>

            <span
              style={{
                display:
                  "block",

                marginTop:
                  2,

                color:
                  "#94a3b8",

                fontSize:
                  10,
              }}
            >
              {memoryData
                ?.source ||
                "Shared Revenue Memory"}
            </span>
          </div>
        </div>

        <span
          style={{
            ...memoryStatusStyle,

            background:
              memoryData
                ?.status ===
              "ERROR"
                ? "rgba(239, 68, 68, 0.14)"
                : "rgba(16, 185, 129, 0.12)",

            color:
              memoryData
                ?.status ===
              "ERROR"
                ? "#fca5a5"
                : "#6ee7b7",
          }}
        >
          {memoryData
            ?.status ===
          "ERROR"
            ? "● ERROR"
            : "● CONNECTED"}
        </span>
      </section>

      <section
        style={
          memoryTimelineShellStyle
        }
      >
        <div
          style={{
            marginBottom:
              20,
          }}
        >
          <span
            style={
              memoryTimelineEyebrowStyle
            }
          >
            SHARED MEMORY TIMELINE
          </span>

          <h2
            style={{
              margin:
                "5px 0 0",

              color:
                "#101828",
            }}
          >
            What RevTrace remembers
          </h2>
        </div>

        {!memoryData ? (
          <div
            style={
              memoryEmptyStyle
            }
          >
            Loading account memory
            trace...
          </div>
        ) : memoryData.status ===
          "ERROR" ? (
          <div
            style={
              memoryErrorStyle
            }
          >
            {
              memoryData.error
            }
          </div>
        ) : sortedEvents.length ===
          0 ? (
          <div
            style={
              memoryEmptyStyle
            }
          >
            No journey memories have
            been recorded for this
            account yet.
          </div>
        ) : (
          <div>

            {sortedEvents.map(
              (
                event,
                index
              ) => (
                <div
                  key={
                    event.event_id ||
                    `${event.event_type}-${index}`
                  }
                  style={{
                    display:
                      "grid",

                    gridTemplateColumns:
                      "44px 1fr",

                    gap:
                      14,

                    position:
                      "relative",

                    paddingBottom:
                      index ===
                      sortedEvents.length -
                        1
                        ? 0
                        : 22,
                  }}
                >
                  <div
                    style={{
                      display:
                        "flex",

                      flexDirection:
                        "column",

                      alignItems:
                        "center",
                    }}
                  >
                    <div
                      style={
                        memoryEventIconStyle
                      }
                    >
                      {eventIcon(
                        event.event_type
                      )}
                    </div>

                    {index !==
                      sortedEvents.length -
                        1 && (
                      <div
                        style={{
                          width:
                            1,

                          flex:
                            1,

                          minHeight:
                            26,

                          background:
                            "#e5e7eb",
                        }}
                      />
                    )}
                  </div>

                  <div
                    style={
                      memoryEventCardStyle
                    }
                  >
                    <div
                      style={
                        memoryEventHeaderStyle
                      }
                    >
                      <div>
                        <strong
                          style={{
                            display:
                              "block",

                            color:
                              "#101828",

                            fontSize:
                              12,
                          }}
                        >
                          {formatStage(
                            event.event_type
                          )}
                        </strong>

                        <span
                          style={{
                            color:
                              "#667085",

                            fontSize:
                              10,
                          }}
                        >
                          {formatStage(
                            event.agent
                          )}
                          {" · "}
                          {formatStage(
                            event.stage
                          )}
                        </span>
                      </div>

                      <span
                        style={{
                          color:
                            "#98a2b3",

                          fontSize:
                            9,

                          whiteSpace:
                            "nowrap",
                        }}
                      >
                        {formatTime(
                          event.created_at
                        )}
                      </span>
                    </div>

                    <p
                      style={{
                        margin:
                          0,

                        color:
                          "#475467",

                        fontSize:
                          11,

                        lineHeight:
                          1.6,
                      }}
                    >
                      {event.summary ||
                        "Journey event retained."}
                    </p>

                    {event.payload &&
                      Object.keys(
                        event.payload
                      ).length >
                        0 && (
                      <details
                        style={{
                          marginTop:
                            10,
                        }}
                      >
                        <summary
                          style={
                            memoryDetailsSummaryStyle
                          }
                        >
                          Memory details
                        </summary>

                        <div
                          style={
                            memoryDetailsGridStyle
                          }
                        >
                          {Object.entries(
                            event.payload
                          ).map(
                            ([
                              key,
                              value,
                            ]) => (
                              <div
                                key={
                                  key
                                }
                                style={
                                  memoryDetailItemStyle
                                }
                              >
                                <span
                                  style={
                                    memoryDetailLabelStyle
                                  }
                                >
                                  {formatStage(
                                    key
                                  )}
                                </span>

                                <strong
                                  style={
                                    memoryDetailValueStyle
                                  }
                                >
                                  {memoryValue(
                                    value
                                  )}
                                </strong>
                              </div>
                            )
                          )}
                        </div>
                      </details>
                    )}
                  </div>
                </div>
              )
            )}

          </div>
        )}
      </section>

    </>
  );
}

function MemoryStat({
  label,
  value,
  icon,
}) {
  return (
    <div
      style={
        memoryStatCardStyle
      }
    >
      <div
        style={
          memoryStatIconStyle
        }
      >
        {icon}
      </div>

      <div>
        <strong
          style={{
            display:
              "block",

            color:
              "#101828",

            fontSize:
              20,
          }}
        >
          {value}
        </strong>

        <span
          style={{
            display:
              "block",

            marginTop:
              2,

            color:
              "#667085",

            fontSize:
              9,
          }}
        >
          {label}
        </span>
      </div>
    </div>
  );
}

function AnalyticsPage({
  accounts,
  stats,
  pipeline,
}) {
  const total =
    accounts.length;

  const completed =
    stats.won +
    stats.lost;

  const winRate =
    completed > 0
      ? Math.round(
          (
            stats.won /
            completed
          ) *
            100
        )
      : 0;

  return (
    <>

      <section
        className={
          styles.pageHeader
        }
      >
        <div>
          <span
            className={
              styles.eyebrow
            }
          >
            REVENUE ANALYTICS
          </span>

          <h1>
            Pipeline intelligence.
          </h1>

          <p>
            Live account statistics
            calculated from RevTrace Core.
          </p>
        </div>
      </section>

      <section
        className={
          styles.kpiGrid
        }
      >
        <KpiCard
          icon="◎"
          value={
            total
          }
          label="Total Accounts"
          sub="All RevTrace journeys"
          color="blue"
        />

        <KpiCard
          icon="✓"
          value={
            stats.won
          }
          label="Won"
          sub="Successful outcomes"
          color="green"
        />

        <KpiCard
          icon="×"
          value={
            stats.lost
          }
          label="Lost"
          sub="Closed-lost journeys"
          color="orange"
        />

        <KpiCard
          icon="%"
          value={`${winRate}%`}
          label="Closed Deal Win Rate"
          sub="Won / completed deals"
          color="purple"
        />
      </section>

      <section
        className={
          styles.analyticsCard
        }
      >
        <h2>
          Current Pipeline
        </h2>

        <div
          className={
            styles.analyticsBars
          }
        >
          {pipeline.map(
            (item) => {
              const maxValue =
                Math.max(
                  ...pipeline.map(
                    (p) =>
                      p.value
                  ),
                  1
                );

              const width =
                item.value === 0
                  ? 0
                  : Math.max(
                      6,
                      (
                        item.value /
                        maxValue
                      ) *
                        100
                    );

              return (
                <div
                  key={
                    item.label
                  }
                  className={
                    styles.analyticsBarRow
                  }
                >
                  <span>
                    {
                      item.label
                    }
                  </span>

                  <div
                    className={
                      styles.analyticsTrack
                    }
                  >
                    <div
                      className={
                        styles.analyticsFill
                      }
                      style={{
                        width:
                          `${width}%`,
                      }}
                    />
                  </div>

                  <strong>
                    {
                      item.value
                    }
                  </strong>
                </div>
              );
            }
          )}
        </div>
      </section>

    </>
  );
}

function KpiCard({
  icon,
  value,
  label,
  sub,
  color,
}) {
  return (
    <div
      className={
        styles.kpiCard
      }
    >
      <div
        className={`${styles.kpiIcon} ${styles[color]}`}
      >
        {icon}
      </div>

      <div
        className={
          styles.kpiContent
        }
      >
        <strong>
          {value}
        </strong>

        <span>
          {label}
        </span>

        <small>
          {sub}
        </small>
      </div>
    </div>
  );
}

function ContextRow({
  label,
  value,
  strong,
}) {
  return (
    <div
      className={
        styles.contextRow
      }
    >
      <span>
        {label}
      </span>

      <strong
        className={
          strong
            ? styles.contextStrong
            : ""
        }
      >
        {value}
      </strong>
    </div>
  );
}

function ActivityItem({
  event,
}) {
  return (
    <div
      className={
        styles.activityItem
      }
    >
      <div
        className={
          styles.activityDot
        }
      />

      <div
        className={
          styles.activityContent
        }
      >
        <div
          className={
            styles.activityTitleRow
          }
        >
          <strong>
            {formatStage(
              event.event_type
            )}
          </strong>

          <span>
            {formatTime(
              event.created_at
            )}
          </span>
        </div>

        <p>
          {formatStage(
            event.agent
          )}
        </p>

        <small>
          {
            event.summary
          }
        </small>
      </div>
    </div>
  );
}

function AgentStage({
  number,
  type,
  title,
  purpose,
  items,
  output,
  onClick,
}) {
  return (
    <button
      className={`${styles.agentStage} ${styles[`${type}Border`]}`}
      onClick={
        onClick
      }
    >
      <div
        className={
          styles.agentStageTop
        }
      >
        <span
          className={`${styles.agentNumber} ${styles[type]}`}
        >
          {number}
        </span>

        <div>
          <h3>
            {title}
          </h3>

          <p>
            {purpose}
          </p>
        </div>
      </div>

      <ul>
        {items.map(
          (item) => (
            <li
              key={
                item
              }
            >
              ✓ {item}
            </li>
          )
        )}
      </ul>

      <div
        className={`${styles.agentOutput} ${styles[type]}`}
      >
        Output: {output}
      </div>
    </button>
  );
}

function EmptyState({
  title,
  text,
  action,
}) {
  return (
    <div
      className={
        styles.emptyState
      }
    >
      <div
        className={
          styles.emptyIcon
        }
      >
        ◎
      </div>

      <h3>
        {title}
      </h3>

      <p>
        {text}
      </p>

      <button
        onClick={
          action
        }
      >
        Create Prospect
      </button>
    </div>
  );
}

const memoryShellStyle = {
  background:
    "#ffffff",

  border:
    "1px solid #e5e7eb",

  borderRadius:
    16,

  padding:
    20,

  marginBottom:
    22,

  boxShadow:
    "0 8px 30px rgba(15, 23, 42, 0.05)",
};

const memorySelectorStyle = {
  display:
    "flex",

  justifyContent:
    "space-between",

  alignItems:
    "center",

  gap:
    20,

  flexWrap:
    "wrap",
};

const memoryLabelStyle = {
  display:
    "block",

  color:
    "#98a2b3",

  fontSize:
    10,

  textTransform:
    "uppercase",

  letterSpacing:
    "0.08em",

  marginBottom:
    5,
};

const memoryAccountNameStyle = {
  display:
    "block",

  color:
    "#101828",

  fontSize:
    20,
};

const memoryMetaStyle = {
  display:
    "block",

  color:
    "#667085",

  fontSize:
    11,

  marginTop:
    5,
};

const memorySelectStyle = {
  minWidth:
    300,

  padding:
    "11px 14px",

  border:
    "1px solid #d0d5dd",

  borderRadius:
    9,

  background:
    "#ffffff",

  color:
    "#101828",

  outline:
    "none",
};

const memoryStatsGridStyle = {
  display:
    "grid",

  gridTemplateColumns:
    "repeat(auto-fit, minmax(170px, 1fr))",

  gap:
    14,

  marginBottom:
    22,
};

const memoryProviderStyle = {
  display:
    "flex",

  alignItems:
    "center",

  justifyContent:
    "space-between",

  gap:
    20,

  background:
    "#0f172a",

  color:
    "#ffffff",

  borderRadius:
    14,

  padding:
    "16px 20px",

  marginBottom:
    22,
};

const memoryProviderIconStyle = {
  width:
    36,

  height:
    36,

  display:
    "grid",

  placeItems:
    "center",

  borderRadius:
    10,

  background:
    "rgba(249, 115, 22, 0.15)",

  color:
    "#fb923c",
};

const memoryStatusStyle = {
  padding:
    "6px 10px",

  borderRadius:
    999,

  fontSize:
    10,

  fontWeight:
    700,
};

const memoryTimelineShellStyle = {
  background:
    "#ffffff",

  border:
    "1px solid #e5e7eb",

  borderRadius:
    16,

  padding:
    22,

  boxShadow:
    "0 8px 30px rgba(15, 23, 42, 0.05)",
};

const memoryTimelineEyebrowStyle = {
  color:
    "#f97316",

  fontSize:
    10,

  fontWeight:
    800,

  letterSpacing:
    "0.1em",

  textTransform:
    "uppercase",
};

const memoryEmptyStyle = {
  padding:
    45,

  textAlign:
    "center",

  color:
    "#98a2b3",
};

const memoryErrorStyle = {
  padding:
    30,

  border:
    "1px solid #fecaca",

  borderRadius:
    12,

  background:
    "#fef2f2",

  color:
    "#b42318",
};

const memoryEventIconStyle = {
  width:
    36,

  height:
    36,

  borderRadius:
    10,

  display:
    "grid",

  placeItems:
    "center",

  background:
    "#fff7ed",

  color:
    "#f97316",

  border:
    "1px solid #fed7aa",

  fontWeight:
    800,

  zIndex:
    2,
};

const memoryEventCardStyle = {
  border:
    "1px solid #eaecf0",

  borderRadius:
    12,

  padding:
    "15px 17px",

  background:
    "#fcfcfd",
};

const memoryEventHeaderStyle = {
  display:
    "flex",

  alignItems:
    "flex-start",

  justifyContent:
    "space-between",

  gap:
    15,

  marginBottom:
    8,
};

const memoryDetailsSummaryStyle = {
  cursor:
    "pointer",

  color:
    "#f97316",

  fontSize:
    9,

  fontWeight:
    700,
};

const memoryDetailsGridStyle = {
  display:
    "grid",

  gridTemplateColumns:
    "repeat(auto-fit, minmax(150px, 1fr))",

  gap:
    8,

  marginTop:
    10,
};

const memoryDetailItemStyle = {
  padding:
    9,

  borderRadius:
    8,

  background:
    "#ffffff",

  border:
    "1px solid #eaecf0",
};

const memoryDetailLabelStyle = {
  display:
    "block",

  color:
    "#98a2b3",

  fontSize:
    8,

  textTransform:
    "uppercase",

  marginBottom:
    3,
};

const memoryDetailValueStyle = {
  color:
    "#344054",

  fontSize:
    9,

  wordBreak:
    "break-word",
};

const memoryStatCardStyle = {
  background:
    "#ffffff",

  border:
    "1px solid #e5e7eb",

  borderRadius:
    13,

  padding:
    16,

  display:
    "flex",

  alignItems:
    "center",

  gap:
    12,

  boxShadow:
    "0 5px 20px rgba(15, 23, 42, 0.04)",
};

const memoryStatIconStyle = {
  width:
    36,

  height:
    36,

  display:
    "grid",

  placeItems:
    "center",

  borderRadius:
    10,

  background:
    "#fff7ed",

  color:
    "#f97316",

  fontWeight:
    800,
};

export default App;