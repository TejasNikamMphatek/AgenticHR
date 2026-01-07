if (!frappe.user.has_role("System Manager") || frappe.user.has_role("Administrator")) {
    window.location.replace('/app/pipal-employee-dashboard')
} else if (frappe.user.has_role(["HR Manager", "Accounts"])) {

    frappe.pages['pipal-hr-dashboard'].on_page_load = function (wrapper) {
        var page = frappe.ui.make_app_page({
            parent: wrapper,
            title: 'Pipal HR Dashboard',
            single_column: true
        });
        me = frappe.pipal_hr_dashboard;
        frappe.pipal_hr_dashboard.make(page);
    };

    frappe.pipal_hr_dashboard = {
        start: 0,
        pending_confirmation: '',
        resign_count: '',
        att_req_count: '',
        leave_app_count: '',
        help_desk_count: '',
        anniver_slide: '',
        birthday_slide: '',
        user_profile: '',
        make: function (page) {
            var me = frappe.pipal_hr_dashboard;
            me.page = page;
            me.run();
        },
        run: function () {
            var me = frappe.pipal_hr_dashboard;
            frappe.call({
                method: "hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.getDashboardData",
                args: {
                    start: me.start,
                },
                callback: function (response) {
                    if (response.message && response.message.length > 0) {
                        me.send_data(response.message);
                        response.message.forEach(function (d) {
                            if (d) {
                            } else {
                                frappe.show_alert({ message: __("Data Not Found ! "), indicator: "gray" });
                            }
                        });
                    } else {
                        frappe.show_alert({ message: __("No more updates"), indicator: "gray" });
                        me.more.parent().addClass("hidden");
                    }
                },
            });
            $('.page-head').addClass('hide');
        },
    send_data: function (data) {
            // Ensure 'me' refers to our object instance
            var me = frappe.pipal_hr_dashboard;

            me.pending_confirmation = data[0]['probation_employee'].length;
            me.resign_count = data[0]['resign_emp'].length;
            me.att_req_count = data[0]['attendance_req'].length;
            me.leave_app_count = data[0]['leave_application'].length;
            me.help_desk_count = data[0]['help_desk_request'].length;
            
            // Generate sliders
            me.anniver_slide = me.anniEmpSlider(data[0]['anni_emp']);
            me.birthday_slide = me.birthdayEmpSlider(data[0]['birthday_employee']);
            
            me.showGreeting();
            me.user_profile = me.showUserProfile(data[0]['login_user']);

            // IMPORTANT: Pass 'me' into the template context explicitly
            // This allows the HTML template to see the counts (me.resign_count, etc.)
            $(frappe.render_template("pipal_hr_dashboard", {
                data: data,
                me: me
            })).appendTo(me.page.main);

            me.runSlides();
            me.showHideSlider(data[0]['anni_emp'], data[0]['birthday_employee']);
            
            // Initialize AI listeners
            me.init_agent_listeners();
        },
run_ai_onboarding: function () {
            const me = this;

            const chatbox = document.getElementById("ai-chatbot-box");
            if (chatbox) chatbox.classList.remove("hidden");

            const messages = document.getElementById("ai-chat-messages");
            if (messages) messages.innerHTML = "";

            frappe.call({
                method: "hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.start_ai_onboarding",
                callback: function (r) {
                    if (r.message) {
                        me.add_ai_message(r.message);
                    }
                }
            });
        },

        init_agent_listeners: function () {
            const me = this;

            frappe.realtime.on('show_agent_dialog', (data) => {
                me.current_agent_question = data;
                document.getElementById("ai-chatbot-box")?.classList.remove("hidden");
                me.add_ai_message(`Please enter ${data.field}`);
            });
            frappe.realtime.on('employee_completed_event', (data) => {
                console.log("Realtime signal received!", data);
                    // Show a standard Frappe Alert
                    frappe.show_alert({
                        message: __(data.message),
                        indicator: "green"
                    }, 7);
                    if (me.refresh) me.refresh(); 
                });

            frappe.realtime.on('ai_agent_completed', () => {
                setTimeout(() => {
                    document.getElementById("ai-chatbot-box")?.classList.add("hidden");
                    me.current_agent_question = null;
                    document.getElementById("ai-chat-messages").innerHTML = "";
                    document.getElementById("ai-chat-input").value = "";
                    if (cur_list) cur_list.refresh();
                }, 500);
            });

            frappe.realtime.on('ai_agent_error', (data) => {
                frappe.show_alert({
                    message: __(data.msg || "Error during onboarding"),
                    indicator: "red"
                });
                document.getElementById("ai-chatbot-box")?.classList.add("hidden");
                me.current_agent_question = null;
            });
            
        },
       
        
        send_ai_answer: function () {
            const input = document.getElementById("ai-chat-input");
            const answer = input.value.trim();
            if (!answer || !me.current_agent_question) return;

            me.add_user_message(answer);
            input.value = "";

            frappe.call({
                method: "hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.send_answer_to_agent",
                args: {
                    cache_key: me.current_agent_question.cache_key,
                    answer: answer
                }
            });
        },

        handle_ai_enter: function (e) {
            if (e.key === "Enter") {
                this.send_ai_answer();
            }
        },

        add_ai_message: function (text) {
            const box = document.getElementById("ai-chat-messages");
            const div = document.createElement("div");
            div.className = "ai-message";
            div.innerText = text;
            box.appendChild(div);
        },

        add_user_message: function (text) {
            const box = document.getElementById("ai-chat-messages");
            const div = document.createElement("div");
            div.className = "user-message";
            div.innerText = text;
            box.appendChild(div);
        },
        employee_created_alert:function(message){
            console.log(message)
        },

        // === AI AGENT FUNCTIONS END ===

        anniEmpSlider: function (anni_emp) {
            let slide = '';
            let isActiveSet = false;

            for (let i = 0; i < anni_emp.length; i++) {
                emp_image = anni_emp[i]['image'] || '/assets/hrms/images/user_employee.png';

                if (anni_emp[i]['employee_completed_year'] == 0) {
                    continue;
                }

                slide += `
                    <div class="carousel-item ${!isActiveSet ? 'active' : ''}" data-interval="1000">
                        <div class="card text-center p-2">
                            <div class="text-center">
                                <img width="50px" src="${emp_image}" />
                            </div>
                            <b>${anni_emp[i]['employee_completed_year']} Year Completed</b><br>
                            <p>Yay! Today is ${anni_emp[i]['employee_name']} Work Anniversary</p><br>
                            <button class="btn btn-info btn-sm btn-send-wish" onclick="me.sendAnniversaryWish(${anni_emp[i]['employee']})">
                                Send a Wish!
                            </button>
                        </div>
                    </div>
                `;

                isActiveSet = true;
            }

            return slide;
        },

        birthdayEmpSlider: function (birthday_emp) {
            slide = '';
            for (let i = 0; i < birthday_emp.length; i++) {
                emp_image = birthday_emp[i]['image'] || '/assets/hrms/images/user_employee.png';
                slide += `  <div class="carousel-item ${i == 0 ? 'active' : ''}" data-interval="1000">
                                <div class="card  text-center p-2">
                                    <div class="text-center">
                                        <img width="50px" src="${emp_image}" />
                                    </div>
                                    <strong>Happy Birthday</strong> <br>
                                    <p>Yay ! Today is ${birthday_emp[i]['employee_name']} Birthday</p>
                                    <br>
                                    <button class="btn btn-info btn-sm btn-send-wish" onclick = "me.sendBirthdayWish(${birthday_emp[i]['employee']})">
                                        Send a Wish!
                                    </button>
                                </div>
                            </div>  `
            }
            return slide;
        },

        sendAnniversaryWish: function (wish_emp) {
            frappe.call(`hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.sendAnniversaryWish`, {
                employee: wish_emp
            });
        },

        sendToAllAnniversaryWish: function () {
            frappe.call(`hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.sendToAllAnniversaryWish`, {});
        },

        sendBirthdayWish: function (birth_emp) {
            frappe.call(`hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.sendBirthdayWish`, {
                employee: birth_emp
            });
        },

        sendToAllBirthDayWish: function () {
            frappe.call(`hrms.hr.page.pipal_hr_dashboard.pipal_hr_dashboard.sendToAllBirthdayWish`, {});
        },

        showHideSlider: function (anni_arr = [], birth_arr = []) {
            if (anni_arr.length < 1 || me.anniver_slide == "") {
                $('.anniver_slide').hide()
            }
            if (birth_arr.length < 1) {
                $('.birthday_slide').hide()
            }
        },

        displayGreeting: function (greeting) {
            if (hour < 12) {
                greeting = "Good Morning";
            } else if (hour < 17) {
                greeting = "Good Afternoon";
            } else {
                greeting = "Good Evening";
            }
            return greeting
        },

        showGreeting: function () {
            greetingMessage = "Good Morning";
            now = new Date();
            hour = now.getHours();
            minute = now.getMinutes();
            seconds = now.getSeconds();
            
            dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
            dayOfMonth = now.getDate();
            monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
            month = monthNames[now.getMonth()];
            year = now.getFullYear();

            greetingMessage = me.displayGreeting(greetingMessage);
        },

        runSlides() {
            setInterval(() => {
                $('#carouselAnniversaryInterval').carousel({
                    interval: 1000
                });
                $('#carouselBirthdayInterval').carousel({
                    interval: 1000
                });
            }, 3000);
        },

        showUserProfile: function (user_data) {
            user_image = user_data[0]['user_image'] || "/assets/hrms/images/user_employee.png";
            role_profile = user_data[0]['role_profile_name'] || "";
            user_profile = `
            <div class="user-info">
                <div class="image">
                    <a href=""><img src="${user_image}" alt="User"></a>
                </div>
                <div class="detail">
                    <h4>${user_data[0]['full_name']}</h4>
                    <small>${role_profile}</small>                        
                </div>
                <a href="javascript:void(0);" class="fullscreen hidden-sm-down" data-provide="fullscreen" data-close="true"><i class="zmdi zmdi-fullscreen"></i></a>
                <a href="javascript:void(0);" class="js-right-sidebar" data-close="true"><i class="zmdi zmdi-settings zmdi-hc-spin"></i></a>
            </div>
            `;
            return user_profile;
        }
    }
} else {
    frappe.show_alert({ message: __("Role Not Defined .... !"), indicator: "red" });
}